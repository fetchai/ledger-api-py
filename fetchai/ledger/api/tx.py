import base64
import binascii

from .common import ApiEndpoint


class TransactionApi(ApiEndpoint):

    def status(self, tx_digest):
        """
        Determines the status of the transaction at the node

        :param tx_digest: The base64 encoded string of the target tx digest
        :return:
        """

        # for the moment get requests must use the hex encoded hash name
        tx_digest_hex = binascii.hexlify(base64.b64decode(tx_digest)).decode()

        url = 'http://{}:{}/api/status/tx/{}'.format(self.host, self.port, tx_digest_hex)

        response = self._session.get(url).json()
        return response.get('status')
