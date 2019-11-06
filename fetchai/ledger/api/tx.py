import base64

from .common import ApiEndpoint


class TxStatus:
    _SUCCESSFUL_TERMINAL_STATES = ('Executed', 'Submitted')
    _NON_TERMINAL_STATES = ('Unknown', 'Pending')

    def __init__(self,
                 digest: bytes,
                 status: str,
                 exit_code: int,
                 charge: int,
                 charge_rate: int,
                 fee: int):
        self._digest_bytes = digest
        self._digest_hex = self._digest_bytes.hex()
        self.status = status
        self.exit_code = exit_code
        self.charge = charge
        self.charge_rate = charge_rate
        self.fee = fee

    @property
    def successful(self):
        return self.status in self._SUCCESSFUL_TERMINAL_STATES

    @property
    def failed(self):
        return self.status not in self._NON_TERMINAL_STATES and \
               self.status not in self._SUCCESSFUL_TERMINAL_STATES

    @property
    def digest_hex(self):
        return self._digest_hex

    @property
    def digest_bytes(self):
        return self._digest_bytes


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
            digest=base64.b64decode(response['tx'].encode()),
            status=str(response['status']),
            exit_code=int(response['exit_code']),
            charge=int(response['charge']),
            charge_rate=int(response['charge_rate']),
            fee=int(response['fee']))
