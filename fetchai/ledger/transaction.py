import io
import logging
import random
from collections import OrderedDict
from io import BytesIO
from typing import Union

from fetchai.ledger.crypto import Entity
from fetchai.ledger.serialisation import transaction, integer, identity, bytearray
from fetchai.ledger.serialisation.transaction import decode_transaction, decode_payload
from .bitvector import BitVector
from .crypto import Address, Identity

Identifier = Union[Address, Identity]
AddressLike = Union[Address, Identity, str, bytes]


class Transaction:
    def __init__(self):
        self._from = None
        self._transfers = OrderedDict()
        self._valid_from = 0
        self._valid_until = 0
        self._charge_rate = 0
        self._charge_limit = 0

        self._contract_digest = None
        self._contract_address = None
        self._counter = random.getrandbits(64)
        self._chain_code = None
        self._shard_mask = BitVector()
        self._action = None
        self._metadata = {
            'synergetic_data_submission': False
        }
        self._data = b''

        self._signers = OrderedDict()

    @property
    def from_address(self) -> Address:
        return self._from

    @from_address.setter
    def from_address(self, address: Identifier):
        self._from = Address(address)

    @property
    def transfers(self):
        return self._transfers

    @property
    def valid_from(self):
        return self._valid_from

    @valid_from.setter
    def valid_from(self, block_number: int):
        self._valid_from = int(block_number)

    @property
    def valid_until(self):
        return self._valid_until

    @valid_until.setter
    def valid_until(self, block_number: int):
        self._valid_until = int(block_number)

    @property
    def charge_rate(self):
        return self._charge_rate

    @charge_rate.setter
    def charge_rate(self, charge: int):
        self._charge_rate = int(charge)

    @property
    def charge_limit(self):
        return self._charge_limit

    @charge_limit.setter
    def charge_limit(self, limit: int):
        self._charge_limit = int(limit)

    @property
    def contract_digest(self):
        return self._contract_digest

    @property
    def contract_address(self):
        return self._contract_address

    @property
    def counter(self):
        return self._counter

    @counter.setter
    def counter(self, value: int):
        self._counter = int(value)

    @property
    def chain_code(self):
        return self._chain_code

    @property
    def shard_mask(self):
        return self._shard_mask

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, name):
        self._action = str(name)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data: bytes):
        self._data = bytes(data)

    def compare(self, other: 'Transaction') -> bool:
        if not self.from_address == other.from_address:
            return False
        if not self.transfers == other.transfers:
            return False
        if not self.valid_from == other.valid_from:
            return False
        if not self.valid_until == other.valid_until:
            return False
        if not self.charge_rate == other.charge_rate:
            return False
        if not self.charge_limit == other.charge_limit:
            return False
        if not self.contract_digest == other.contract_digest:
            return False
        if not self.contract_address == other.contract_address:
            return False
        if not self.chain_code == other.chain_code:
            return False
        if not self.action == other.action:
            return False
        if not self.shard_mask == other.shard_mask:
            return False
        if not self.data == other.data:
            return False
        if not self.signers.keys() == other.signers.keys():
            return False
        if not self.counter == other.counter:
            return False
        if not self._metadata == other._metadata:
            return False
        if not self.payload == other.payload:
            return False
        return True

    @property
    def payload(self):
        buffer = BytesIO()
        transaction.encode_payload(buffer, self)
        return buffer.getvalue()

    @staticmethod
    def from_payload(payload: bytes):
        return decode_payload(io.BytesIO(payload))

    @staticmethod
    def from_encoded(encoded_transaction: bytes):
        valid, tx = decode_transaction(io.BytesIO(encoded_transaction))
        if valid:
            return tx
        else:
            return None

    @property
    def signers(self):
        return self._signers

    def add_transfer(self, address: Identifier, amount: int):
        assert amount > 0

        # ensure the address is correct
        address = Address(address)
        self._transfers[address] = self._transfers.get(address, 0) + amount

    def target_contract(self, address: Address, mask: BitVector):
        self._contract_address = Address(address)
        self._shard_mask = BitVector(mask)
        self._chain_code = None

    def target_chain_code(self, chain_code_id: str, mask: BitVector):
        self._contract_digest = None
        self._contract_address = None
        self._shard_mask = BitVector(mask)
        self._chain_code = str(chain_code_id)

    @property
    def synergetic_data_submission(self):
        return self._metadata['synergetic_data_submission']

    @synergetic_data_submission.setter
    def synergetic_data_submission(self, is_submission):
        self._metadata['synergetic_data_submission'] = is_submission

    def add_signer(self, signer: Identity):
        if signer not in self._signers:
            self._signers[signer] = {}  # will be replaced with a signature in the future

    def sign(self, signer: Entity):
        if Identity(signer) in self._signers:
            signature = signer.sign(self.payload)
            self._signers[Identity(signer)] = {
                'signature': signature,
                'verified': signer.verify(self.payload, signature)
            }

    def merge_signatures(self, tx2: 'Transaction'):
        if self.payload != tx2.payload:
            logging.warning("Attempting to combine transactions with different payloads")
            return None

        for signer, signature in tx2.signers.items():
            if signature and not self.signers[signer]:
                self.signers[signer] = signature

    def encode_partial(self):
        buffer = BytesIO()
        transaction.encode_payload(buffer, self)

        num_signed = len([s for s in self.signers.values() if s])
        integer.encode(buffer, num_signed)

        for signer, sig in self.signers.items():
            if sig:
                identity.encode(buffer, signer)
                bytearray.encode(buffer, sig['signature'])

        return buffer.getvalue()

    @staticmethod
    def decode_partial(data: bytes):
        buffer = io.BytesIO(data)

        tx = decode_payload(buffer)

        num_sigs = integer.decode(buffer)

        for i in range(num_sigs):
            signer = identity.decode(buffer)
            signature = bytearray.decode(buffer)
            tx.signers[signer] = {'signature': signature,
                                  'verified': signer.verify(tx.payload, signature)}

        if not all(s['verified'] for s in tx.signers.values() if 'verified' in s):
            logging.warning("Some signatures failed to verify")

        return tx
