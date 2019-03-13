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
from fetch.ledger.serialisation.objects.transaction_api import create_wealth_tx, create_transfer_tx
from fetch.ledger.crypto.signing import Signing


class TokenApi(ApiEndpoint):
    API_PREFIX = 'fetch.token'

    def balance(self, address):
        """
        Query the balance for a given address from the remote node

        :param address: The base64 encoded string containing the address of the node
        :return: The balance value retried
        :raises: ApiError on any failures
        """

        # format and make the request
        request = {
            'address': address
        }
        success, data = self._post_json('balance', request)

        # check for error cases
        if not success:
            raise ApiError('Failed to request balance for address ' + address)

        if 'balance' not in data:
            raise ApiError('Malformed response from server')

        # return the balance
        return int(data['balance'])

    def wealth(self, private_key_bin, amount, fee=0):
        """
        Creates wealth for specified account

        :param private_key_bin: The bytes of the private key of the targeted address
        :param amount: The amount of wealth to be generated
        :param fee: The fee value to be used for the transaction
        :return: True if successful, otherwise False
        """

        # extract keys
        signing_key = Signing.create_private_key(private_key_bin)
        verifying_key = signing_key.get_verifying_key()

        # format and sign the transaction
        tx = create_wealth_tx(verifying_key.to_string(), amount, fee)
        tx.sign(signing_key)

        # submit the transaction
        self._post_tx(tx.to_wire_format(), 'wealth')

    def transfer(self, private_key_bin, to_address, amount, fee=0):
        """
        Transfers wealth from one account to another account

        :param private_key_bin: The bytes of the private key of the source address
        :param to_address: The bytes of the targeted address to send funds to
        :param amount: The amount of funds being transfered
        :param fee: The fee associated with the transfer
        :return: True if successful, otherwise False
        """

        # extract keys
        signing_key = Signing.create_private_key(private_key_bin)
        verifying_key = signing_key.get_verifying_key()

        # format the sign the transaction
        tx = create_transfer_tx(verifying_key.to_string(), to_address, amount, fee=fee)
        tx.sign(signing_key)

        # submit the transaction
        self._post_tx(tx.to_wire_format(), 'transfer')

