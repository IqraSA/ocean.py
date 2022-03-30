#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.structures.file_objects import UrlFile
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import get_wallet


@pytest.fixture
def publish_market_wallet():
    return get_wallet(4)


@pytest.fixture
def consume_market_wallet():
    return get_wallet(5)


# - [ ] Publish Market Swap Fee
# - [ ] Publish Market Order Fee (absolute amount)
# - [ ] Consume Market Swap Fee
# - [ ] Consume Market Order Fee
# - [ ] OPC Swap Fee (Approved Token) == 0.1%
# - [ ] OPC Swap Fee (Non-approved Token)== 0.2%
# - [ ] OPC Consume Fee
# LP Swap Fee
# Provider Fee (Cost per MB, Cost per min)
# OPC Provider Fee


def create_pool_with_fees(
    ocean: Ocean,
    publisher: Wallet,
    publish_market_address: str,
    publish_market_order_fee_token: str,
    publish_market_order_fee_amount: int,
    publish_market_swap_fee: int,
    lp_swap_fee: int,
):
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }

    file1 = UrlFile(
        url="https://raw.githubusercontent.com/tbertinmahieux/MSongsDB/master/Tasks_Demos/CoverSongs/shs_dataset_test.txt"
    )
    encrypted_files = ocean.assets.encrypt_files([file1])

    asset = ocean.assets.create(
        metadata=metadata,
        publisher_wallet=publisher,
        encrypted_files=encrypted_files,
        erc721_name="NFTToken1",
        erc721_symbol="NFT1",
        erc721_uri="https://oceanprotocol.com/nft/",
        erc20_templates=[1],
        erc20_names=["Datatoken1"],
        erc20_symbols=["DT1"],
        erc20_minters=[publisher.address],
        erc20_fee_managers=[publisher.address],
        erc20_publishing_market_addresses=[publish_market_address],
        fee_token_addresses=[publish_market_order_fee_token],
        erc20_cap_values=[ocean.to_wei(1_000)],
        publishing_fee_amounts=[publish_market_order_fee_amount],
        erc20_bytess=[b""],
        encrypt_flag=True,
        compress_flag=True,
    )

    service = asset.get_service_by_index(0)
    factory_router = ocean.factory_router()
    return ocean.create_pool(
        erc20_token=ocean.get_datatoken(service.datatoken),
        base_token=ocean.OCEAN_token,
        rate=ocean.to_wei(1),
        vesting_amount=ocean.to_wei(1000),
        vested_blocks=factory_router.get_min_vesting_period(),
        initial_liq=ocean.to_wei(1),
        lp_swap_fee=lp_swap_fee,
        market_swap_fee=publish_market_swap_fee,
        market_fee_collector=publish_market_address,
        from_wallet=publisher,
    )


@pytest.mark.skip
def test_pool_fees(
    publisher_ocean_instance: Ocean,
    publisher_wallet: Wallet,
    publish_market_wallet: Wallet,
):
    pool = create_pool_with_fees(
        ocean=publisher_ocean_instance,
        publisher=publisher_wallet,
        publish_market_address=publish_market_wallet.address,
        publish_market_order_fee_token=publisher_ocean_instance.OCEAN_address,
        publish_market_order_fee_amount=10,
        publish_market_swap_fee=publisher_ocean_instance.to_wei("0.001"),  # 0.1%
        lp_swap_fee=publisher_ocean_instance.to_wei("0.01"),  # 1%
    )

    # Create asset with download service and compute service

    # Check fee related events are emitted

    # Check fees

    # Check amount in out

    # Swap amount in out

    # Check fee releated events are emitted

    # Check amounts

    # Order

    # Check fee related events are emitted

    # Check amounts