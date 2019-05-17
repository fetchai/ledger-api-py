from collections import OrderedDict
from typing import Union

from .bitvector import BitVector
from .crypto import Address, Identity

Identifier = Union[Address, Identity]


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
        self._chain_code = None
        self._shard_mask = BitVector()
        self._action = None
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
        self._chain_code = str(chain_code_id)
        self._shard_mask = BitVector(mask)

    def add_signer(self, signer: Identity):
        if signer not in self._signers:
            self._signers[signer] = None  # will be replaced with a signature in the future
