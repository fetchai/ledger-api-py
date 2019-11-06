import json
from typing import Union, List, Dict, Optional

from fetchai.ledger.crypto import Address, Identity
from .common import ApiEndpoint

AddressLike = Union[Address, Identity, bytes, str]


class TxContents:
    def __init__(self,
                 digest: bytes,
                 action: str,
                 chain_code: str,
                 from_address: AddressLike,
                 contract_digest: str,
                 contract_address: Optional[AddressLike],
                 valid_from: int,
                 valid_until: int,
                 charge: int,
                 charge_limit: int,
                 transfers: List[Dict[str, Union[str, int]]],
                 signatories: List[str],
                 data: str
                 ):
        self._digest_bytes = digest
        self._digest_hex = self._digest_bytes.hex()
        self.action = action
        self.chain_code = chain_code
        self.from_address = Address(from_address)
        self.contract_digest = contract_digest if contract_digest else None
        self.contract_address = Address(contract_address) if contract_address else None
        self.valid_from = valid_from
        self.valid_until = valid_until
        self.charge = charge
        self.charge_limit = charge_limit
        self.transfers = {Address(t['to']): t['amount'] for t in transfers}
        self.signatories = signatories
        self.data = data

    def transfers_to(self, address: AddressLike) -> int:
        """Returns the amount of FET transferred to an address by this transaction, if any"""
        address = Address(address)
        return self.transfers.get(address, 0)

    @staticmethod
    def from_json(data: Union[dict, str]):
        """Creates a TxContents from a json string or dict object"""
        if isinstance(data, str):
            data = json.loads(data)

        # Extract contents from json, converting as necessary
        return TxContents(
            bytes.fromhex(data.get('digest').lstrip('0x')),
            data.get('action'),
            data.get('chainCode'),
            data.get('from'),
            data.get('contractDigest'),
            data.get('contractAddress'),
            int(data.get('validFrom', 0)),
            int(data.get('validUntil', 0)),
            int(data.get('charge')),
            int(data.get('chargeLimit')),
            [t for t in data.get('transfers')],
            data.get('signatories'),
            data.get('data')
        )


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

    def contents(self, tx_digest) -> TxContents:
        """
        Returns the contents of the transaction at the node

        :param tx_digest: The hex-encoded string of the target tx digest
        :return: TxContents object
        """

        return self._contents(tx_digest)

    def _contents(self, tx_digest) -> TxContents:
        url = 'http://{}:{}/api/tx/{}'.format(self.host, self.port, tx_digest)

        response = self._session.get(url).json()

        return TxContents.from_json(response)
