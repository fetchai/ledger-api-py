import io
import logging
import random
from collections import OrderedDict
from typing import Union, Optional, Dict

from fetchai.ledger.crypto import Entity
from fetchai.ledger.serialisation import transaction
from .bitvector import BitVector
from .crypto import Address, Identity

Identifier = Union[Address, Identity]
AddressLike = Union[Address, Identity, str, bytes]


class Transaction:
    def __init__(self):
        self._from: Optional[Address] = None
        self._transfers: OrderedDict = OrderedDict()
        self._valid_from: int = 0
        self._valid_until: int = 0
        self._charge_rate: int = 0
        self._charge_limit: int = 0
        self._counter: bytes = random.getrandbits(64)
        self._contract_address: Optional[Address] = None
        self._chain_code: Optional[str] = None
        self._shard_mask = BitVector()
        self._action: Optional[str] = None
        self._data = b''
        self._signatures: Dict[Identity, bytes] = OrderedDict()

        # TODO: Not sure about this data submission stuff - talk to AB
        self._metadata = {
            'synergetic_data_submission': False
        }

    def __eq__(self, other):
        if isinstance(other, Transaction):
            return all([
                self.from_address == other.from_address,
                self.transfers == other.transfers,
                self.valid_from == other.valid_from,
                self.valid_until == other.valid_until,
                self.charge_rate == other.charge_rate,
                self.charge_limit == other.charge_limit,
                self.counter == other.counter,
                self.contract_address == other.contract_address,
                self.chain_code == other.chain_code,
                self.shard_mask == other.shard_mask,
                self.action == other.action,
                self.data == other.data,
                self.all_signers2 == other.all_signers2,
                self._metadata == other._metadata, # TODO: This might be removed
                #self._encode_payload() == other._encode_payload(),
                # TODO: This check sort of overrides all of the above checks
            ])
        return False

    def __ne__(self, other):
        return not (self == other)

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

    # TODO: Rename
    @property
    def all_signers2(self):
        return set(self._signatures.keys())

    # TODO: Rename
    @property
    def pending_signers2(self):
        pending = set()
        for identity, signature in self.signatures:
            if len(signature) == 0:
                pending.add(identity)
        return pending

    # TODO: Rename
    @property
    def present_signers(self):
        return self.all_signers2 - self.pending_signers2

    # TODO: Rename
    @property
    def signers(self):
        return list(self._signatures.keys())

    @property
    def signatures(self):
        return self._signatures.items()

    @property
    def is_incomplete(self):
        return len(self.all_signers2) > 0 and len(self.pending_signers2) > 0

    def is_valid(self) -> bool:
        payload = self.encode_payload()
        for identity, signature in self.signatures:
            if not identity.verify(payload, signature):
                return False

        return True

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
        signer = Identity(signer)
        if signer not in self._signatures:
            self._signatures[signer] = bytes()  # will be replaced with a signature in the future

    # TODO: Rename back
    def sign2(self, signer: Entity):
        self.add_signature(Identity(signer), signer.sign(self.encode_payload()))

    # TODO: Find global identity which is causing all the issues and rename
    def add_signature(self, identity: Identity, signature: bytes):
        if identity not in self._signatures:
            raise RuntimeError('Identity is not currently part')
        self._signatures[identity] = signature

    def merge_signatures(self, other_tx: 'Transaction') -> bool:

        # sanity check - make sure the encoded transaction is the same
        if self != other_tx:
            logging.warning("Attempting to combine transactions with different payloads")
            return False

        payload = self.encode_payload()

        # evaluate the signature from the other transaction and build a (more) complete set of signatures
        success = None
        for identity, signature_data in other_tx.signatures:
            if identity in self._signatures:

                # expect zero length signatures from partial transactions, this is not a failure case
                if len(signature_data) == 0:
                    continue

                # validate the signature
                if not identity.verify(payload, signature_data):
                    success = False
                    continue

                # add the signature to the transaction
                self._signatures[identity] = signature_data

                if success is None:
                    success = True

        # if no signatures were merged then this is actually an error
        if success is None:
            success = False

        return success

    def encode_payload(self):
        return transaction.encode_payload2(self)

    # TODO: Rename
    def encode_partial2(self) -> bytes:
        return transaction.encode_transaction2(self)

    # TODO: Rename
    @staticmethod
    def decode_partial2(data: bytes) -> (bool, 'Transaction'):
        return transaction.decode_transaction(io.BytesIO(data))

    # TODO: Rename
    def encode2(self) -> Optional[bytes]:
        if self.is_incomplete:
            return None
        else:
            return transaction.encode_transaction2(self)

    # TODO: Rename
    @staticmethod
    def decode2(encoded_transaction: bytes) -> Optional['Transaction']:
        valid, tx = transaction.decode_transaction(io.BytesIO(encoded_transaction))
        if valid:
            return tx
        else:
            return None

    @staticmethod
    def decode_payload(payload: bytes):
        return transaction.decode_payload(io.BytesIO(payload))
