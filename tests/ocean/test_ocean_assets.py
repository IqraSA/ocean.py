#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging
import uuid

import pytest
from ocean_lib.web3_internal.exceptions import OceanDIDNotFound
from ocean_lib.web3_internal.wallet import Wallet
from ocean_utils.agreements.service_factory import ServiceDescriptor
from ocean_utils.ddo.ddo import DDO
from ocean_utils.did import DID

from tests.resources.helper_functions import (
    get_algorithm_ddo,
    get_computing_metadata,
    get_resource_path,
    get_publisher_wallet)


def create_asset(publisher_ocean_instance):
    ocn = publisher_ocean_instance
    sample_ddo_path = get_resource_path('ddo', 'ddo_sa_sample.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    publisher = get_publisher_wallet()

    asset = DDO(json_filename=sample_ddo_path)
    asset.metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    my_secret_store = 'http://myownsecretstore.com'
    auth_service = ServiceDescriptor.authorization_service_descriptor(my_secret_store)
    return ocn.assets.create(asset.metadata, publisher, [auth_service])


def test_register_asset(publisher_ocean_instance):
    logging.debug("".format())
    sample_ddo_path = get_resource_path('ddo', 'ddo_sa_sample.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    ##########################################################
    # Setup account
    ##########################################################
    publisher = get_publisher_wallet()

    ##########################################################
    # Create an asset DDO with valid metadata
    ##########################################################
    asset = DDO(json_filename=sample_ddo_path)
    asset.metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    ddo = publisher_ocean_instance.assets.create(asset.metadata, publisher)
    publisher_ocean_instance.assets.retire(ddo.did)


def test_resolve_did(publisher_ocean_instance, metadata):
    # prep ddo
    # metadata = Metadata.get_example()
    publisher = get_publisher_wallet()
    # happy path
    original_ddo = publisher_ocean_instance.assets.create(metadata, publisher)
    did = original_ddo.did
    ddo = publisher_ocean_instance.assets.resolve(did).as_dictionary()
    original = original_ddo.as_dictionary()
    assert ddo['publicKey'] == original['publicKey']
    assert ddo['authentication'] == original['authentication']
    assert ddo['service']
    assert original['service']
    metadata = ddo['service'][0]['attributes']
    if 'datePublished' in metadata['main']:
        metadata['main'].pop('datePublished')
    assert ddo['service'][0]['attributes']['main']['name'] == \
        original['service'][0]['attributes']['main']['name']
    assert ddo['service'][1] == original['service'][1]

    # Can't resolve unregistered asset
    unregistered_did = DID.did({"0": "0x00112233445566"})
    with pytest.raises(ValueError):
        publisher_ocean_instance.assets.resolve(unregistered_did)

    # Raise error on bad did
    invalid_did = "did:op:0123456789"
    with pytest.raises(ValueError):
        publisher_ocean_instance.assets.resolve(invalid_did)
    publisher_ocean_instance.assets.retire(did)


def test_create_data_asset(publisher_ocean_instance, consumer_ocean_instance):
    """
    Setup accounts and asset, register this asset on Aquarius (MetaData store)
    """
    pub_ocn = publisher_ocean_instance
    cons_ocn = consumer_ocean_instance

    logging.debug("".format())
    sample_ddo_path = get_resource_path('ddo', 'ddo_sa_sample.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    ##########################################################
    # Setup 2 accounts
    ##########################################################
    aquarius_acct = get_publisher_wallet()

    ##########################################################
    # Create an Asset with valid metadata
    ##########################################################
    asset = DDO(json_filename=sample_ddo_path)
    asset.metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())

    ##########################################################
    # List currently published assets
    ##########################################################
    meta_data_assets = pub_ocn.assets.search('')
    if meta_data_assets:
        print("Currently registered assets:")
        print(meta_data_assets)

    if asset.did in meta_data_assets:
        pub_ocn.assets.resolve(asset.did)
        pub_ocn.assets.retire(asset.did)
    # Publish the metadata
    new_asset = pub_ocn.assets.create(asset.metadata, aquarius_acct)

    # get_asset_metadata only returns 'main' key, is this correct?
    published_metadata = cons_ocn.assets.resolve(new_asset.did)

    assert published_metadata
    # only compare top level keys
    assert sorted(list(asset.metadata['main'].keys())).remove('files') == sorted(
        list(published_metadata.metadata.keys())).remove('encryptedFiles')
    publisher_ocean_instance.assets.retire(new_asset.did)


def test_asset_owner(publisher_ocean_instance):
    ocn = publisher_ocean_instance

    sample_ddo_path = get_resource_path('ddo', 'ddo_sa_sample.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    publisher = get_publisher_wallet()

    asset = DDO(json_filename=sample_ddo_path)
    asset.metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    my_secret_store = 'http://myownsecretstore.com'
    auth_service = ServiceDescriptor.authorization_service_descriptor(my_secret_store)
    new_asset = ocn.assets.create(asset.metadata, publisher, [auth_service])

    assert ocn.assets.owner(new_asset.did) == publisher.address
    publisher_ocean_instance.assets.retire(new_asset.did)


def test_owner_assets(publisher_ocean_instance):
    ocn = publisher_ocean_instance
    publisher = get_publisher_wallet()
    assets_owned = len(ocn.assets.owner_assets(publisher.address))
    asset = create_asset(publisher_ocean_instance)
    assert len(ocn.assets.owner_assets(publisher.address)) == assets_owned + 1
    publisher_ocean_instance.assets.retire(asset.did)


def test_ocean_assets_resolve(publisher_ocean_instance, metadata):
    publisher = get_publisher_wallet()
    ddo = publisher_ocean_instance.assets.create(metadata, publisher)
    ddo_resolved = publisher_ocean_instance.assets.resolve(ddo.did)
    assert ddo.did == ddo_resolved.did
    publisher_ocean_instance.assets.retire(ddo.did)


def test_ocean_assets_search(publisher_ocean_instance, metadata):
    publisher = get_publisher_wallet()
    ddo = publisher_ocean_instance.assets.create(metadata, publisher)
    assert len(publisher_ocean_instance.assets.search('Monkey')) > 0
    publisher_ocean_instance.assets.retire(ddo.did)


def test_ocean_assets_validate(publisher_ocean_instance, metadata):
    assert publisher_ocean_instance.assets.validate(metadata)


def test_ocean_assets_algorithm(publisher_ocean_instance):
    # Allow publish an algorithm
    publisher = get_publisher_wallet()
    metadata = get_algorithm_ddo()['service'][0]
    metadata['attributes']['main']['files'][0]['checksum'] = str(uuid.uuid4())
    ddo = publisher_ocean_instance.assets.create(metadata['attributes'], publisher)
    assert ddo
    publisher_ocean_instance.assets.retire(ddo.did)


def test_ocean_assets_compute(publisher_ocean_instance):
    publisher = get_publisher_wallet()
    metadata = get_computing_metadata()
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    ddo = publisher_ocean_instance.assets.create(metadata, publisher)
    assert ddo
    publisher_ocean_instance.assets.retire(ddo.did)