from .common import ApiEndpoint


class TransactionApi(ApiEndpoint):
    def status(self, tx_digest):
        """
        Determines the status of the transaction at the node

        :param tx_digest: The hex-encoded string of the target tx digest
        :return:
        """

        url = 'http://{}:{}/api/status/tx/{}'.format(self.host, self.port, tx_digest)

        response = self._session.get(url).json()
        return response.get('status')
