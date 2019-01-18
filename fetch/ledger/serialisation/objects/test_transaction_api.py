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
import unittest

from fetch.ledger.crypto import Signing
from fetch.ledger.serialisation.objects.transaction_api import create_transfer_contract, \
    decode_transfer_contract, \
    create_wealth_contract, \
    decode_wealth_contract, \
    create_transfer_tx, \
    create_wealth_tx


class TransactionAPITest(unittest.TestCase):

    def setUp(self):
        self.private_key_0 = Signing.create_private_key(
            base64.b64decode("7fDTiiCsCKG43Z8YlNelveKGwir6EpCHUhrcHDbFBgg="))
        self.private_key_1 = Signing.create_private_key(
            base64.b64decode("Lw1VCeY6gn8k8IRlD+TeadxN0BXGibBQWN9hst+qvFs="))

        self.public_key_bin_0 = self.private_key_0.get_verifying_key().to_string()
        self.public_key_bin_1 = self.private_key_1.get_verifying_key().to_string()

    def _verify_transfer_contract(self, contract_data, exp_address_from_bin, exp_address_to_bin, exp_amount):
        rec_addrs_from, rec_addrs_to, rec_amount = decode_transfer_contract(contract_data)

        assert exp_address_from_bin == rec_addrs_from
        assert exp_address_to_bin == rec_addrs_to
        assert exp_amount == rec_amount

    def test_transfer_contract_create_decode_cycle(self):
        amount = 12345
        address_from_bin = self.public_key_bin_0
        address_to_bin = self.public_key_bin_1

        # PRODUCTION CODE UNDER TEST
        contract_data = create_transfer_contract(address_from_bin=address_from_bin, address_to_bin=address_to_bin,
                                                 amount=amount)

        self._verify_transfer_contract(contract_data, exp_address_from_bin=address_from_bin,
                                       exp_address_to_bin=address_to_bin, exp_amount=amount)

    def test_create_transfer_transaction(self):
        amount = 12345
        fee = 26
        private_key = self.private_key_0
        address_from_bin = self.public_key_bin_0
        address_to_bin = self.public_key_bin_1
        assert address_from_bin != address_to_bin

        # PRODUCTION CODE UNDER TEST
        tx = create_transfer_tx(address_from_bin=address_from_bin, address_to_bin=address_to_bin, amount=amount,
                                fee=fee)
        tx.sign(private_key)

        self._verify_transfer_contract(tx.data, exp_address_from_bin=address_from_bin,
                                       exp_address_to_bin=address_to_bin, exp_amount=amount)
        assert address_from_bin in tx.resources
        assert address_to_bin in tx.resources
        assert 2 == len(tx.resources)
        assert fee == tx.fee
        assert tx.verify()

    def _verify_wealth_contract(self, contract_data, exp_address_to_bin, exp_amount):
        rec_addrs_to, rec_amount = decode_wealth_contract(contract_data)

        assert exp_address_to_bin == rec_addrs_to
        assert exp_amount == rec_amount

    def test_wealth_contract_create_decode_cycle(self):
        amount = 12345
        address_to_bin = self.public_key_bin_0

        # PRODUCTION CODE UNDER TEST
        contract_data = create_wealth_contract(address_to_bin=address_to_bin, amount=amount)

        self._verify_wealth_contract(contract_data, exp_address_to_bin=address_to_bin, exp_amount=amount)

    def test_wealth_transfer_transaction(self):
        amount = 12345
        fee = 26
        private_key = self.private_key_0
        address_to_bin = self.public_key_bin_0

        # PRODUCTION CODE UNDER TEST
        tx = create_wealth_tx(address_to_bin=address_to_bin, amount=amount, fee=fee)
        tx.sign(private_key)

        self._verify_wealth_contract(tx.data, exp_address_to_bin=address_to_bin, exp_amount=amount)
        assert address_to_bin in tx.resources
        assert 1 == len(tx.resources)
        assert fee == tx.fee
        assert tx.verify()
