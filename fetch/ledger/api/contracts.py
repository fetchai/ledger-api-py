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

from fetch.ledger.api import ApiEndpoint, ApiError
from fetch.ledger.serialisation.objects.transaction_api import *
from fetch.ledger.crypto.signing import Signing

import base64
import hashlib
import binascii

def create_signed_wealth_transaction(priv_keys_to, amount, fee):
    address_to_bin = priv_keys_to[0].get_verifying_key().to_string()

    tx = create_wealth_tx(address_to_bin, amount, fee)

    for pk in priv_keys_to:
        tx.sign(pk)

    return tx

class SmartContractManager(ApiEndpoint):
    API_PREFIX = 'fetch.smart_contract_manager'
    #API_PREFIX = 'fetch.token'

    def recent_contracts(self):
        print("recent_contracts")

    def add_contract(self, contract_source):
        """
        Add a smart contract to the ledger
        """

        contract_source_b64 = base64.b64encode(contract_source.encode()) # Contract source as base64
        contract_hash_b64   = base64.b64encode(hashlib.sha256(contract_source_b64).digest()) # base64 of sha256 of the contract_source

        contract_source_b64 = contract_source_b64.decode()
        contract_hash_b64   = contract_hash_b64.decode()

        # Generate random pub-private key pair
        priv_key = Signing.generate_private_key()

        address_to_bin = priv_key.get_verifying_key().to_string()

        tx = create_initial_smart_contract_tx(address_to_bin, contract_source_b64, contract_hash_b64)

        tx.sign(priv_key)

        self._post_tx(tx.to_wire_format(), 'create_initial_contract')

        return contract_hash_b64

class SmartContract(ApiEndpoint):
    API_PREFIX = '???'

    def __init__(self, host, port, pubkey_b64, contract_hash_b64):
        ApiEndpoint.__init__(self, host, port)

        self._pubkey_b64      = pubkey_b64
        self._contract_hash_b64 = contract_hash_b64
        contract_hash_hex = binascii.hexlify(contract_hash_b64.encode()).decode()

        print(contract_hash_hex)

        self.API_PREFIX   = '0x{}.0x{}'.format(contract_hash_hex, pubkey_b64)

        print("API : {}".format(self.API_PREFIX))

    def run_speculative(self, resources=None, function_name="main"):
        priv_key = Signing.generate_private_key()

        address_to_bin = priv_key.get_verifying_key().to_string()

        tx = create_smart_contract_tx(self._contract_hash_b64, self._pubkey_b64, resources, function_name)

        tx.sign(priv_key)

        speculative_output = self._post_tx_speculative(tx.to_wire_format(), function_name)

        return speculative_output.json()

    def run(self, resources=None, function_name="main"):
        priv_key = Signing.generate_private_key()

        address_to_bin = priv_key.get_verifying_key().to_string()

        tx = create_smart_contract_tx(self._contract_hash_b64, self._pubkey_b64, resources, function_name)

        tx.sign(priv_key)

        self._post_tx(tx.to_wire_format(), function_name)

    def output(self):
        return "nothing"

