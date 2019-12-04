import io
import logging
import random
from collections import OrderedDict
from io import BytesIO
from typing import Union, Optional, List

from fetchai.ledger.crypto import Entity
from fetchai.ledger.crypto.deed import Deed
from fetchai.ledger.serialisation import transaction
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

    def target_contract(self, digest: Address, address: Address, mask: BitVector):
        self._contract_digest = Address(digest)
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
            self._signers[signer] = None  # will be replaced with a signature in the future

    def sign(self, signer: Entity):
        if Identity(signer) in self._signers:
            self._signers[Identity(signer)] = {
                'signature': signer.sign(self._payload)
            }

class TransactionBuilder:
    @staticmethod
    def wealth():
        pass


class TransactionFactory:
    @staticmethod
    def wealth(api: 'TokenApi', entity: Entity, amount: int):

        # build up the basic transaction information
        tx = api._create_action_tx(1, entity, 'wealth')
        tx.add_signer(entity)

        # format the transaction payload
        tx.data = api._encode_json({
            'address': entity.public_key,
            'amount': amount
        })

        return tx

    @staticmethod
    def deed(api: 'TokenApi', entity: Entity, deed: Deed, signatories: list = None):
        tx = api._create_action_tx(10000, entity, 'deed')

        if signatories:
            for sig in signatories:
                tx.add_signer(sig)
        else:
            tx.add_signer(entity)

        deed_json = deed.deed_creation_json()

        tx.data = api._encode_json(deed_json)

        return tx

    @staticmethod
    def transfer(api: 'TokenApi', entity: Entity, to: AddressLike, amount: int, fee: int, signatories: list = None):

        # build up the basic transaction information
        tx = api._create_skeleton_tx(fee)
        tx.from_address = Address(entity)
        tx.add_transfer(to, amount)

        if signatories:
            for ent in signatories:
                tx.add_signer(ent)
        else:
            tx.add_signer(entity)

        return tx

    @staticmethod
    def add_stake(api: 'TokenApi', entity: Entity, amount: int, fee: int):

        # build up the basic transaction information
        tx = api._create_action_tx(fee, entity, 'addStake')
        tx.add_signer(entity)

        # format the transaction payload
        tx.data = api._encode_json({
            'address': entity.public_key,
            'amount': amount
        })

        return tx

    @staticmethod
    def de_stake(api: 'TokenApi', entity: Entity, amount: int, fee: int):

        # build up the basic transaction information
        tx = api._create_action_tx(fee, entity, 'deStake')
        tx.add_signer(entity)

        # format the transaction payload
        tx.data = api._encode_json({
            'address': entity.public_key,
            'amount': amount
        })

        return tx

    @staticmethod
    def collect_stake(api: 'TokenApi', entity: Entity, fee: int):

        # build up the basic transaction information
        tx = api._create_action_tx(fee, entity, 'collectStake')
        tx.add_signer(entity)

        return tx

    class Contract:
        @staticmethod
        def action(api: 'ContractsApi',
                   contract_digest: Address, contract_address: Address, action: str,
                   fee: int, from_address: Address, signers: List[Entity], *args,
                   shard_mask: Optional[BitVector] = None) -> Transaction:

            # Default to wildcard shard mask if none supplied
            if not shard_mask:
                logging.warning("Defaulting to wildcard shard mask as none supplied")
                shard_mask = BitVector()

            # build up the basic transaction information
            tx = api._create_skeleton_tx(fee)
            tx.from_address = Address(from_address)
            tx.target_contract(contract_digest, contract_address, shard_mask)
            tx.action = str(action)
            tx.data = api._encode_msgpack_payload(*args)

            for signer in signers:
                tx.add_signer(signer)

            return tx

        @staticmethod
        def create(api: 'ContractsApi', owner: Entity, contract: 'Contract', fee: int,
                   shard_mask: Optional[BitVector] = None) -> Transaction:
            # Default to wildcard shard mask if none supplied
            if not shard_mask:
                logging.warning("Defaulting to wildcard shard mask as none supplied")
                shard_mask = BitVector()

            # build up the basic transaction information
            tx = api._create_skeleton_tx(fee)
            tx.from_address = Address(owner)
            tx.target_chain_code(api.API_PREFIX, shard_mask)
            tx.action = 'create'
            tx.data = api._encode_json({
                'nonce': contract.nonce,
                'text': contract.encoded_source,
                'digest': contract.digest.to_hex()
            })
            tx.add_signer(owner)

            return tx
