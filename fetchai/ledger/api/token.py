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
from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Address, Entity, Identity
from fetchai.ledger.serialisation import encode_transaction
from fetchai.ledger.transaction import Transaction

AddressLike = Union[Address, Identity, str, bytes]


class TokenApi(ApiEndpoint):
    API_PREFIX = 'fetch.token'

    def balance(self, address: AddressLike):
        """
        Query the balance for a given address from the remote node

        :param address: The base64 encoded string containing the address of the node
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

    def wealth(self, entity: Entity, amount: int):
        """
        Creates wealth for specified account

        :param private_key_bin: The bytes of the private key of the targeted address
        :param amount: The amount of wealth to be generated
        :param fee: The fee value to be used for the transaction
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """
        ENDPOINT = 'wealth'

        # format the data to be closed by the transaction

        # wildcard for the moment
        shard_mask = BitVector()

        # build up the basic transaction information
        tx = Transaction()
        tx.from_address = Address(entity)
        tx.valid_until = 10000
        tx.charge_rate = 1
        tx.charge_limit = 10
        tx.target_chain_code(self.API_PREFIX, shard_mask)
        tx.action = 'wealth'
        tx.add_signer(entity)

        # format the transaction payload
        tx.data = self._encode_json({
            'address': entity.public_key,
            'amount': amount
        })

        # encode and sign the transaction
        encoded_tx = encode_transaction(tx, [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def transfer(self, entity: Entity, to: AddressLike, amount: int, fee: int):
        """
        Transfers wealth from one account to another account

        :param private_key_bin: The bytes of the private key of the source address
        :param to_address: The bytes of the targeted address to send funds to
        :param amount: The amount of funds being transfered
        :param fee: The fee associated with the transfer
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """
        ENDPOINT = 'transfer'

        # format the data to be closed by the transaction

        # wildcard for the moment
        shard_mask = BitVector()

        # build up the basic transaction information
        tx = Transaction()
        tx.from_address = Address(entity)
        tx.valid_until = 10000
        tx.charge_rate = 1
        tx.charge_limit = fee
        tx.add_transfer(to, amount)
        tx.add_signer(entity)

        # encode and sign the transaction
        encoded_tx = encode_transaction(tx, [entity])

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)
