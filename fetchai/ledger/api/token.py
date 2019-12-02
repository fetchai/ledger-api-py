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
from typing import Union

from fetchai.ledger.api import ApiEndpoint, ApiError
from fetchai.ledger.crypto import Address, Entity, Identity
from fetchai.ledger.crypto.deed import Deed
from fetchai.ledger.serialisation import transaction
from fetchai.ledger.transaction import TransactionFactory

AddressLike = Union[Address, Identity, str, bytes]


class TokenApi(ApiEndpoint):
    API_PREFIX = 'fetch.token'

    def balance(self, address: AddressLike):
        """
        Query the balance for a given address from the remote node

        :param address: The base58 encoded string containing the address of the node
        :return: The balance value retried
        :raises: ApiError on any failures
        """

        # convert the input to an address
        address = Address(address)

        # format and make the request
        request = {
            'address': str(address)
        }
        success, data = self._post_json('balance', request)

        # check for error cases
        if not success:
            raise ApiError('Failed to request balance for address ' + str(address))

        if 'balance' not in data:
            raise ApiError('Malformed response from server')

        # return the balance
        return int(data['balance'])

    def stake(self, address: AddressLike):
        """
        Query the stake for a given address from the remote node

        :param address: The base58 encoded string containing the address of the node
        :return: The balance value retried
        :raises: ApiError on any failures
        """

        # convert the input to an address
        address = Address(address)

        # format and make the request
        request = {
            'address': str(address)
        }
        success, data = self._post_json('stake', request)

        # check for error cases
        if not success:
            raise ApiError('Failed to request balance for address ' + str(address))

        if 'stake' not in data:
            raise ApiError('Malformed response from server')

        # return the balance
        return int(data['stake'])

    def stake_cooldown(self, address: AddressLike):
        """
        Query the stake on cooldown for a given address from the remote node

        :param address: The base58 encoded string containing the address of the node
        :return: The balance value retried
        :raises: ApiError on any failures
        """

        # convert the input to an address
        address = Address(address)

        # format and make the request
        request = {
            'address': str(address)
        }
        success, data = self._post_json('cooldownStake', request)

        # check for error cases
        if not success:
            raise ApiError('Failed to request cooldown stake for address ' + str(address))

        if 'cooldownStake' not in data:
            raise ApiError('Malformed response from server')

        # return the result
        return data

    def wealth(self, entity: Entity, amount: int):
        ENDPOINT = 'wealth'

        tx = TransactionFactory.wealth(self, entity, amount)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx, [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def deed(self, entity: Entity, deed: Deed, signatories: list = None):
        ENDPOINT = 'deed'

        tx = TransactionFactory.deed(self, entity, deed, signatories)

        encoded_tx = transaction.encode_transaction(tx, signatories if signatories else [entity])

        return self._post_tx_json(encoded_tx, ENDPOINT)

    def transfer(self, entity: Entity, to: AddressLike, amount: int, fee: int, signatories: list = None):
        ENDPOINT = 'transfer'

        tx = TransactionFactory.transfer(self, entity, to, amount, fee, signatories)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx, signatories if signatories else [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def add_stake(self, entity: Entity, amount: int, fee: int):
        ENDPOINT = 'addStake'

        tx = TransactionFactory.add_stake(self, entity, amount, fee)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx, [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def de_stake(self, entity: Entity, amount: int, fee: int):
        ENDPOINT = 'deStake'

        tx = TransactionFactory.de_stake(self, entity, amount, fee)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx, [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def collect_stake(self, entity: Entity, fee: int):
        ENDPOINT = 'collectStake'

        tx = TransactionFactory.collect_stake(self, entity, fee)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx, [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)


