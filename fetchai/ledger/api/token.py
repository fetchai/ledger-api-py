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
from typing import Union, Dict

from fetchai.ledger.api import ApiEndpoint, ApiError
from fetchai.ledger.crypto import Address, Entity, Identity
from fetchai.ledger.crypto.deed import Deed
from fetchai.ledger.serialisation import transaction
from fetchai.ledger.serialisation.transaction import encode_multisig_transaction
from fetchai.ledger.transaction import TransactionFactory, Transaction

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
        """
        Creates wealth for specified account

        :param entity: The entity object to create wealth for
        :param amount: The amount of wealth to be generated
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        ENDPOINT = 'wealth'

        tx = TransactionFactory.wealth(self, entity, amount)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx, [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def deed(self, entity: Entity, deed: Deed, signatories: list = None):
        """
        Sets the deed for a multi-sig account

        :param entity: The entity object to create wealth for
        :param deed: The deed to set
        :param signatories: The entities that will sign this action
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        ENDPOINT = 'deed'

        tx = TransactionFactory.deed(self, entity, deed, signatories)

        encoded_tx = transaction.encode_transaction(tx, signatories if signatories else [entity])

        return self._post_tx_json(encoded_tx, ENDPOINT)

    def transfer(self, entity: Entity, to: AddressLike, amount: int, fee: int, signatories: list = None):
        """
        Transfers wealth from one account to another account

        :param entity: The entity from which to transfer funds
        :param to: The bytes of the targeted address to send funds to
        :param amount: The amount of funds being transfered
        :param fee: The fee associated with the transfer
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        ENDPOINT = 'transfer'

        tx = TransactionFactory.transfer(self, entity, to, amount, fee, signatories)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx, signatories if signatories else [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def add_stake(self, entity: Entity, amount: int, fee: int):
        """
        Stakes a specific amount of

        :param entity: The entity object that desires to stake
        :param amount: The amount to stake
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        ENDPOINT = 'addStake'

        tx = TransactionFactory.add_stake(self, entity, amount, fee)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx, [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def de_stake(self, entity: Entity, amount: int, fee: int):
        """
        Destakes a specific amount of tokens from a staking miner. This will put the
        tokens in a cool down period

        :param entity: The entity object that desires to destake
        :param amount: The amount of tokens to destake
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        ENDPOINT = 'deStake'

        tx = TransactionFactory.de_stake(self, entity, amount, fee)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx, [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def collect_stake(self, entity: Entity, fee: int):
        """
        Collect all stakes that have reached the end of the cooldown period

        :param entity: The entity object that desires to collect
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        ENDPOINT = 'collectStake'

        tx = TransactionFactory.collect_stake(self, entity, fee)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx, [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def submit_signed_tx(self, tx: Transaction, signatures: Dict[Identity, bytes]):
        """
        Appends signatures to a transaction and submits it, returning the transaction digest
        :param tx: A pre-assembled transaction
        :param signatures: A dict of signers signatures
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """
        # Encode transaction and append signatures
        encoded_tx = encode_multisig_transaction(tx, signatures)

        # Submit and return digest
        return self._post_tx_json(encoded_tx, tx.action)
