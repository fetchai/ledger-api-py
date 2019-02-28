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

class SmartContractManager(ApiEndpoint):
    API_PREFIX = 'fetch.smart_contract_manager'

    def add_contract(self, contract_source):
        """
        Add a smart contract to the ledger
        """

        contract_source_b64 = base64.b64encode(contract_source.encode()) # Contract source as base64
        contract_hash_b64   = base64.b64encode(hashlib.sha256(contract_source_b64).digest()) # base64 of sha256 of the contract_source

        contract_source_b64 = contract_source_b64.decode()
        contract_hash_b64   = contract_hash_b64.decode()

        # Generate random pub-private key pair for this submission
        priv_key = Signing.generate_private_key()

        address_to_bin = priv_key.get_verifying_key().to_string()

        tx = create_initial_smart_contract_tx(address_to_bin, contract_source_b64, contract_hash_b64)

        tx.sign(priv_key)

        self._post_tx(tx.to_wire_format(), 'create_initial_contract')

        return contract_hash_b64

class SmartContract(ApiEndpoint):
    API_PREFIX = 'NOT_SET'

    def __init__(self, host, port, pubkey_b64, contract_hash_b64):
        ApiEndpoint.__init__(self, host, port)

        self._pubkey_b64      = pubkey_b64
        self._contract_hash_b64 = contract_hash_b64

        # For the http request, it is less error prone to send the contract reference as 0xHEX
        contract_hash_hex = binascii.hexlify(contract_hash_b64.encode()).decode()

        self.API_PREFIX   = '0x{}.0x{}'.format(contract_hash_hex, pubkey_b64)

    def run_speculative(self, resources=None, function_name="main"):
        """
        Submit a call to a smart contract speculatively - this allows the user
        to determine if signing, formatting, resource locking etc. will be successful.
        """
        priv_key = Signing.generate_private_key()

        address_to_bin = priv_key.get_verifying_key().to_string()

        tx = create_smart_contract_tx(self._contract_hash_b64, self._pubkey_b64, resources, function_name)

        tx.sign(priv_key)

        speculative_output = self._post_tx_speculative(tx.to_wire_format(), function_name)

        return speculative_output.json()

    # Create a TX that runs this smart contract, calling a specific function
    def run(self, resources=None, function_name="main"):
        priv_key = Signing.generate_private_key()

        address_to_bin = priv_key.get_verifying_key().to_string()

        tx = create_smart_contract_tx(self._contract_hash_b64, self._pubkey_b64, resources, function_name)

        tx.sign(priv_key)

        self._post_tx(tx.to_wire_format(), function_name)
