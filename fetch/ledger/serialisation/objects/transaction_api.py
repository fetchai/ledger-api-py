# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

import base64
import json

from fetch.ledger.serialisation.objects.transaction import Tx


def create_wealth_contract(address_to_bin, amount):
    contract = {
        "address": base64.b64encode(address_to_bin).decode(),
        "amount": amount
    }
    contract_json_str = json.dumps(contract)
    return contract_json_str.encode()

# Create an initial contract
def create_initial_contract(address_to_bin, source_b64, hash_b64):
    contract = {
        "address": base64.b64encode(address_to_bin).decode(),
        "contract_source_b64" : source_b64,
        "contract_hash_b64" : hash_b64
    }
    contract_json_str = json.dumps(contract)
    return contract_json_str.encode()

def create_contract(contract_hash_b64):
    contract = {
        "contract_hash_b64" : contract_hash_b64
    }
    contract_json_str = json.dumps(contract)
    return contract_json_str.encode()


def decode_wealth_contract(contract_data):
    contract_json_str = contract_data.decode()
    contract = json.loads(contract_json_str)

    address_to_b64 = contract["address"]
    amount = contract["amount"]

    address_to_bin = base64.b64decode(address_to_b64)
    return (address_to_bin, amount)


def create_transfer_contract(address_from_bin, address_to_bin, amount):
    contract = {
        "from": base64.b64encode(address_from_bin).decode(),
        "to": base64.b64encode(address_to_bin).decode(),
        "amount": amount
    }
    contract_json_str = json.dumps(contract)
    return contract_json_str.encode()


def decode_transfer_contract(contract_data):
    contract_json_str = contract_data.decode()
    contract = json.loads(contract_json_str)

    address_from_b64 = contract["from"]
    address_to_b64 = contract["to"]
    amount = contract["amount"]

    address_from_bin = base64.b64decode(address_from_b64)
    address_to_bin = base64.b64decode(address_to_b64)
    return (address_from_bin, address_to_bin, amount)


def create_wealth_tx(address_to_bin, amount, fee=0):
    tx = Tx()
    tx.contract_name = b'fetch.token.wealth'
    tx.data = create_wealth_contract(address_to_bin, amount)
    tx.fee = fee
    tx.resources = [address_to_bin]
    return tx


def create_transfer_tx(address_from_bin, address_to_bin, amount, fee=0):
    tx = Tx()
    tx.contract_name = b'fetch.token.transfer'
    tx.data = create_transfer_contract(address_from_bin, address_to_bin, amount)
    tx.fee = fee
    tx.resources = [address_from_bin, address_to_bin]
    return tx

def create_initial_smart_contract_tx(address_of_issuer, source_b64, hash_b64):
    tx = Tx()
    tx.contract_name = b'fetch.smart_contract_manager.create_initial_contract'
    tx.data = create_initial_contract(address_of_issuer, source_b64, hash_b64)
    tx.fee = 10 # TODO(HUT): default fees?
    tx.resources       = [address_of_issuer]
    tx.contract_hashes = [hash_b64.encode()]
    return tx

def create_smart_contract_tx(contract_hash_b64, pubkey_b64, resources, function_name):
    tx = Tx()
    tx.contract_name = "{}.{}.{}".format(contract_hash_b64, pubkey_b64, function_name)
    print("NAME: " + tx.contract_name)
    tx.contract_name = tx.contract_name.encode()
    tx.data = create_contract(contract_hash_b64)
    tx.fee = 10 # TODO(HUT): default fees?
    tx.resources = []

    for res in resources:
        tx.resources += [res.encode()]

    tx.contract_hashes = [contract_hash_b64.encode()]
    return tx
