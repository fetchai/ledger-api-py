# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
from typing import Union, Iterable, Optional

from fetchai.ledger.api import ApiEndpoint, ApiError
from fetchai.ledger.api.common import TransactionFactory, unstable
from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Address, Entity, Identity
from fetchai.ledger.crypto.deed import Deed
from fetchai.ledger.serialisation import transaction

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

    @unstable
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

    @unstable
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

    def deed(self, entity: Entity, deed: Deed, fee: int):
        """
        Sets the deed for a multi-sig account

        :param entity: The entity object to create a deed for
        :param deed: The deed to set
        :param signatories: The entities that will sign this action
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        ENDPOINT = 'deed'

        tx = TokenTxFactory.deed(entity, deed, fee, [entity])
        self._set_validity_period(tx)
        tx.sign(entity)

        encoded_tx = transaction.encode_transaction(tx)

        return self._post_tx_json(encoded_tx, ENDPOINT)

    def transfer(self, entity: Entity, to: AddressLike, amount: int, fee: int):
        """
        Transfers funds from one account to another account

        :param entity: The entity from which to transfer funds
        :param to: The bytes of the targeted address to send funds to
        :param amount: The amount of funds being transfered
        :param fee: The fee associated with the transfer
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        ENDPOINT = 'transfer'

        tx = TokenTxFactory.transfer(entity, to, amount, fee, [entity])
        self._set_validity_period(tx)
        tx.sign(entity)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx)

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    @unstable
    def add_stake(self, entity: Entity, amount: int, fee: int):
        """
        Stakes a specific amount of

        :param entity: The entity object that desires to stake
        :param amount: The amount to stake
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        ENDPOINT = 'addStake'

        tx = TokenTxFactory.add_stake(entity, amount, fee, [entity])
        self._set_validity_period(tx)
        tx.sign(entity)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx)

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    @unstable
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

        tx = TokenTxFactory.de_stake(entity, amount, fee, [entity])
        self._set_validity_period(tx)
        tx.sign(entity)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx)

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    @unstable
    def collect_stake(self, entity: Entity, fee: int):
        """
        Collect all stakes that have reached the end of the cooldown period

        :param entity: The entity object that desires to collect
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        ENDPOINT = 'collectStake'

        tx = TokenTxFactory.collect_stake(entity, fee, [entity])
        self._set_validity_period(tx)
        tx.sign(entity)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx)

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)


class TokenTxFactory(TransactionFactory):
    API_PREFIX = 'fetch.token'

    @classmethod
    def deed(cls, from_address: AddressLike, deed: Optional[Deed], fee: int,
             signatories: Iterable[Identity]) -> 'Transaction':
        # TODO: This is known
        shard_mask = BitVector()

        tx = cls._create_chain_code_action_tx(fee, from_address, 'deed', signatories, shard_mask)
        tx.data = cls._encode_json({} if deed is None else deed.to_json())

        return tx

    @classmethod
    def transfer(cls, from_address: AddressLike, to: AddressLike, amount: int, fee: int,
                 signatories: Iterable[Identity]) -> 'Transaction':
        # build up the basic transaction information
        tx = cls._create_skeleton_tx(fee)
        tx.from_address = Address(from_address)
        tx.add_transfer(to, amount)

        for ident in signatories:
            tx.add_signer(ident)

        return tx

    @classmethod
    @unstable
    def add_stake(cls, identity: Identity, amount: int, fee: int, signatories: Iterable[Identity]) -> 'Transaction':
        # build up the basic transaction information
        tx = cls._create_chain_code_action_tx(fee, identity, 'addStake', signatories, BitVector())

        # format the transaction payload
        tx.data = cls._encode_json({
            'address': identity.public_key,
            'amount': amount
        })

        return tx

    @classmethod
    @unstable
    def de_stake(cls, identity: Identity, amount: int, fee: int, signatories: Iterable[Identity]) -> 'Transaction':
        # build up the basic transaction information
        tx = cls._create_chain_code_action_tx(fee, identity, 'deStake', signatories, BitVector())

        # format the transaction payload
        tx.data = cls._encode_json({
            'address': identity.public_key,
            'amount': amount
        })

        return tx

    @classmethod
    @unstable
    def collect_stake(cls, identity: Identity, fee: int, signatories: Iterable[Identity]) -> 'Transaction':
        # build up the basic transaction information
        return cls._create_chain_code_action_tx(fee, identity, 'collectStake', signatories, BitVector())
