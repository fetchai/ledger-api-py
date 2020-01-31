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
import json
from typing import Union, List, Dict, Optional

from fetchai.ledger.crypto import Address, Identity
from fetchai.ledger.decode import decode_hex_or_b64
from .common import ApiEndpoint

AddressLike = Union[Address, Identity, bytes, str]


class TxStatus:
    _SUCCESSFUL_TERMINAL_STATES = ('Executed', 'Submitted')
    _NON_TERMINAL_STATES = ('Unknown', 'Pending')

    def __init__(self,
                 digest: bytes,
                 status: str,
                 exit_code: int,
                 charge_limit: int,
                 charge_rate: int,
                 fee: int):
        self._digest_bytes = bytes(digest)
        self._digest_hex = self._digest_bytes.hex()
        self.status = str(status)
        self.exit_code = int(exit_code)
        self.charge_limit = int(charge_limit)
        self.charge_rate = int(charge_rate)
        self.fee = int(fee)

    @property
    def successful(self):
        return self.status in self._SUCCESSFUL_TERMINAL_STATES

    @property
    def failed(self):
        return self.status not in self._NON_TERMINAL_STATES and \
               self.status not in self._SUCCESSFUL_TERMINAL_STATES

    @property
    def non_terminal(self):
        return self.status in self._NON_TERMINAL_STATES

    @property
    def digest(self):
        return '0x' + self.digest_hex

    @property
    def digest_hex(self):
        return self._digest_hex

    @property
    def digest_bytes(self):
        return self._digest_bytes


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
    def from_json(data: Union[dict, str]) -> Optional['TxContents']:
        """Creates a TxContents from a json string or dict object"""
        if isinstance(data, str):
            data = json.loads(data)

        # in the case that we query a transaction which might not be present
        if len(data) == 0:
            return None

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

        return self._status(tx_digest)

    def _status(self, tx_digest) -> TxStatus:
        url = '{}://{}:{}/api/status/tx/{}'.format(self.protocol, self.host, self.port, tx_digest)

        response = self._session.get(url).json()

        return TxStatus(
            digest=decode_hex_or_b64(response['tx']),
            status=str(response['status']),
            exit_code=int(response['exit_code']),
            charge_limit=int(response['charge']),
            charge_rate=int(response['charge_rate']),
            fee=int(response['fee']))

    def contents(self, tx_digest) -> Optional[TxContents]:
        """
        Returns the contents of the transaction at the node

        :param tx_digest: The hex-encoded string of the target tx digest
        :return: TxContents object
        """

        return self._contents(tx_digest)

    def _contents(self, tx_digest) -> Optional[TxContents]:
        url = '{}://{}:{}/api/tx/{}'.format(self.protocol, self.host, self.port, tx_digest)

        response = self._session.get(url).json()

        return TxContents.from_json(response)
