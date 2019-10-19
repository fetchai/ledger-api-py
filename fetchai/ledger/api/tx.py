from .common import ApiEndpoint


class TxStatus:
    def __init__(self,
                 digest,
                 status,
                 exit_code,
                 charge,
                 charge_rate,
                 fee):
        self.digest = digest
        self.status = status
        self.exit_code = exit_code
        self.charge = charge
        self.charge_rate = charge_rate
        self.fee = fee

    @property
    def finished(self):
        return self.status not in ('Unknown', 'Pending')


class TransactionApi(ApiEndpoint):
    def status(self, tx_digest):
        """
        Determines the status of the transaction at the node

        :param tx_digest: The hex-encoded string of the target tx digest
        :return:
        """

        return self._status(tx_digest)

    def _status(self, tx_digest):
        url = '{}://{}:{}/api/status/tx/{}'.format(self.protocol, self.host, self.port, tx_digest)

        response = self._session.get(url).json()

        return TxStatus(
            digest=response['tx'],
            status=response['status'],
            exit_code=response['exit_code'],
            charge=response['charge'],
            charge_rate=response['charge_rate'],
            fee=response['fee'])
