#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List

from enforce_typing import enforce_types

from ocean_lib.models import balancer_constants
from ocean_lib.models.v4.btoken import BTokenBase
from ocean_lib.models.v4.models_structures import BPoolInitialized
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class BPool(BTokenBase):
    CONTRACT_NAME = "BPool"

    EVENT_LOG_SWAP = "LOG_SWAP"
    EVENT_LOG_JOIN = "LOG_JOIN"
    EVENT_LOG_EXIT = "LOG_EXIT"
    EVENT_LOG_CALL = "LOG_CALL"
    EVENT_LOG_BPT = "LOG_BPT"

    @property
    def event_LOG_SWAP(self):
        return self.events.LOG_SWAP()

    @property
    def event_LOG_JOIN(self):
        return self.events.LOG_JOIN()

    @property
    def event_LOG_EXIT(self):
        return self.events.LOG_EXIT()

    @property
    def event_LOG_CALL(self):
        return self.events.LOG_CALL()

    @property
    def event_LOG_BPT(self):
        return self.events.LOG_BPT()

    def initialize(
        self, bpool_initialized: BPoolInitialized, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "initialize",
            (
                bpool_initialized.controller,
                bpool_initialized.factory,
                bpool_initialized.swap_fees,
                bpool_initialized.public_swap,
                bpool_initialized.finalized,
                bpool_initialized.tokens,
                bpool_initialized.fee_collectors,
            ),
            from_wallet,
        )

    def setup(
        self,
        data_token: str,
        data_token_amount: int,
        data_token_weight: int,
        base_token: str,
        base_token_amount: int,
        base_token_weight: int,
        swap_fee: int,
        from_wallet: Wallet,
    ) -> str:
        tx_id = self.send_transaction(
            "setup",
            (
                data_token,
                data_token_amount,
                data_token_weight,
                base_token,
                base_token_amount,
                base_token_weight,
                swap_fee,
            ),
            from_wallet,
            {"gas": balancer_constants.GASLIMIT_BFACTORY_NEWBPOOL},
        )

        return tx_id

    def is_public_pool(self) -> bool:
        return self.contract.caller.isPublicSwap()

    def opf_fee(self) -> int:
        return self.contract.caller.getOPFFee()

    def community_fee(self, address: str) -> int:
        return self.contract.caller.communityFees(address)

    def market_fee(self, address: str) -> int:
        return self.contract.caller.marketFees(address)

    def is_finalized(self) -> bool:
        """Returns true if state is finalized.

        The `finalized` state lets users know that the weights, balances, and
        fees of this pool are immutable. In the `finalized` state, `SWAP`,
        `JOIN`, and `EXIT` are public. `CONTROL` capabilities are disabled.
        """
        return self.contract.caller.isFinalized()

    def is_bound(self, token_address: str) -> bool:
        """Returns True if the token is bound.

        A bound token has a valid balance and weight. A token cannot be bound
        without valid parameters which will enable e.g. `getSpotPrice` in terms
        of other tokens. However, disabling `isSwapPublic` will disable any
        interaction with this token in practice (assuming there are no existing
        tokens in the pool, which can always `exitPool`).
        """
        return self.contract.caller.isBound(token_address)

    def get_num_tokens(self) -> int:
        """
        How many tokens are bound to this pool.
        """
        return self.contract.caller.getNumTokens()

    def get_current_tokens(self) -> List[str]:
        """@return -- list of [token_addr:str]"""
        return self.contract.caller.getCurrentTokens()

    def get_final_tokens(self) -> List[str]:
        """@return -- list of [token_addr:str]"""
        return self.contract.caller.getFinalTokens()

    def collect_opf(self, dst: str, from_wallet: Wallet) -> str:
        return self.send_transaction("collectOPF", (dst,), from_wallet)

    def collect_market_fee(self, dst: str, from_wallet: Wallet) -> str:
        return self.send_transaction("collectMarketFee", (dst,), from_wallet)

    def update_market_fee_collector(
        self, new_collector: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "updateMarketFeeCollector", (new_collector,), from_wallet
        )

    def get_denormalized_weight(self, token_address: str) -> int:
        return self.contract.caller.getDenormalizedWeight(token_address)

    def get_total_denormalized_weight(self) -> int:
        return self.contract.caller.getTotalDenormalizedWeight()

    def get_normalized_weight(self, token_address: str) -> int:
        """
        The normalized weight of a token. The combined normalized weights of
        all tokens will sum up to 1. (Note: the actual sum may be 1 plus or
        minus a few wei due to division precision loss)
        """
        return self.contract.caller.getNormalizedWeight(token_address)

    def get_balance(self, token_address: str) -> int:
        return self.contract.caller.getBalance(token_address)

    def get_swap_fee(self) -> int:
        return self.contract.caller.getSwapFee()

    def get_controller(self) -> str:
        """
        Get the "controller" address, which can call `CONTROL` functions like
        `rebind`, `setSwapFee`, or `finalize`.
        """
        return self.contract.caller.getController()

    def get_data_token_address(self) -> str:
        return self.contract.caller.getDataTokenAddress()

    def get_base_token_address(self) -> str:
        return self.contract.caller.getBaseTokenAddress()

    def set_swap_fee(self, swap_fee: int, from_wallet: Wallet) -> str:
        """
        Caller must be controller. Pool must NOT be finalized.
        """
        return self.send_transaction("setSwapFee", (swap_fee,), from_wallet)

    def finalize(self, from_wallet: Wallet) -> str:
        """
        This makes the pool **finalized**. This is a one-way transition. `bind`,
        `rebind`, `unbind`, `setSwapFee` and `setPublicSwap` will all throw
        `ERR_IS_FINALIZED` after pool is finalized. This also switches
        `isSwapPublic` to true.
        """
        return self.send_transaction("finalize", (), from_wallet)

    def bind(
        self, token_address: str, balance: int, weight: int, from_wallet: Wallet
    ) -> str:
        """
        Binds the token with address `token`. Tokens will be pushed/pulled from
        caller to adjust match new balance. Token must not already be bound.
        `balance` must be a valid balance and denorm must be a valid denormalized
        weight. `bind` creates the token record and then calls `rebind` for
        updating pool weights and token transfers.

        Possible errors:
        -`ERR_NOT_CONTROLLER` -- caller is not the controller
        -`ERR_IS_BOUND` -- T is already bound
        -`ERR_IS_FINALIZED` -- isFinalized() is true
        -`ERR_ERC20_FALSE` -- ERC20 token returned false
        -`ERR_MAX_TOKENS` -- Only 8 tokens are allowed per pool
        -unspecified error thrown by token
        """
        return self.send_transaction(
            "bind", (token_address, balance, weight), from_wallet
        )

    def rebind(
        self, token_address: str, balance: int, weight: int, from_wallet: Wallet
    ) -> str:
        """
        Changes the parameters of an already-bound token. Performs the same
        validation on the parameters.
        """
        return self.send_transaction(
            "rebind", (token_address, balance, weight), from_wallet
        )

    def get_spot_price(self, token_in: str, token_out: str) -> int:
        return self.contract.caller.getSpotPrice(token_in, token_out)

    def join_pool(
        self, pool_amount_out: int, max_amounts_in: List[int], from_wallet: Wallet
    ) -> str:
        """
        Join the pool, getting `poolAmountOut` pool tokens. This will pull some
        of each of the currently trading tokens in the pool, meaning you must
        have called `approve` for each token for this pool. These values are
        limited by the array of `maxAmountsIn` in the order of the pool tokens.
        """
        return self.send_transaction(
            "joinPool", (pool_amount_out, max_amounts_in), from_wallet
        )

    def exit_pool(
        self, pool_amount_in: int, min_amounts_out: List[int], from_wallet: Wallet
    ) -> str:
        """
        Exit the pool, paying `poolAmountIn` pool tokens and getting some of
        each of the currently trading tokens in return. These values are
        limited by the array of `minAmountsOut` in the order of the pool tokens.
        """
        return self.send_transaction(
            "exitPool", (pool_amount_in, min_amounts_out), from_wallet
        )

    def swap_exact_amount_in(
        self,
        tokenIn_address: str,
        tokenAmountIn: int,
        tokenOut_address: str,
        minAmountOut: int,
        maxPrice: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Trades an exact `tokenAmountIn` of `tokenIn` taken from the caller by
        the pool, in exchange for at least `minAmountOut` of `tokenOut` given
        to the caller from the pool, with a maximum marginal price of
        `maxPrice`.

        Returns `(tokenAmountOut`, `spotPriceAfter)`, where `tokenAmountOut`
        is the amount of token that came out of the pool, and `spotPriceAfter`
        is the new marginal spot price, ie, the result of `getSpotPrice` after
        the call. (These values are what are limited by the arguments; you are
        guaranteed `tokenAmountOut >= minAmountOut` and
        `spotPriceAfter <= maxPrice)`.
        """
        return self.send_transaction(
            "swapExactAmountIn",
            (tokenIn_address, tokenAmountIn, tokenOut_address, minAmountOut, maxPrice),
            from_wallet,
        )

    def swap_exact_amount_out(
        self,
        tokenIn_address: str,
        maxAmountIn: int,
        tokenOut_address: str,
        tokenAmountOut: int,
        maxPrice: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "swapExactAmountOut",
            (tokenIn_address, maxAmountIn, tokenOut_address, tokenAmountOut, maxPrice),
            from_wallet,
        )

    def join_swap_extern_amount_in(
        self,
        tokenIn_address: str,
        tokenAmountIn: int,
        minPoolAmountOut: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Pay `tokenAmountIn` of token `tokenIn` to join the pool, getting
        `poolAmountOut` of the pool shares.
        """
        return self.send_transaction(
            "joinswapExternAmountIn",
            (tokenIn_address, tokenAmountIn, minPoolAmountOut),
            from_wallet,
        )

    def join_swap_pool_amount_out(
        self,
        tokenIn_address: str,
        poolAmountOut: int,
        maxAmountIn: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Specify `poolAmountOut` pool shares that you want to get, and a token
        `tokenIn` to pay with. This costs `maxAmountIn` tokens (these went
        into the pool).
        """
        return self.send_transaction(
            "joinswapPoolAmountOut",
            (tokenIn_address, poolAmountOut, maxAmountIn),
            from_wallet,
        )

    def exit_swap_pool_amount_in(
        self,
        tokenOut_address: str,
        poolAmountIn: int,
        minAmountOut: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Pay `poolAmountIn` pool shares into the pool, getting `tokenAmountOut`
        of the given token `tokenOut` out of the pool.
        """
        return self.send_transaction(
            "exitswapPoolAmountIn",
            (tokenOut_address, poolAmountIn, minAmountOut),
            from_wallet,
        )

    def exit_swap_extern_amount_out(
        self,
        tokenOut_address: str,
        tokenAmountOut: int,
        maxPoolAmountIn: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Specify `tokenAmountOut` of token `tokenOut` that you want to get out
        of the pool. This costs `poolAmountIn` pool shares (these went into
        the pool).
        """
        return self.send_transaction(
            "exitswapExternAmountOut",
            (tokenOut_address, tokenAmountOut, maxPoolAmountIn),
            from_wallet,
        )