import base64
import hashlib
import json
import logging
from os import urandom
from typing import Union, List, Optional, Iterable

from fetchai.ledger.api.contracts import ContractTxFactory
from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Identity
from fetchai.ledger.parser.etch_parser import EtchParser, UnparsableAddress, UseWildcardShardMask, EtchParserError
from fetchai.ledger.serialisation import sha256_hash
from fetchai.ledger.serialisation.shardmask import ShardMask
from .api import LedgerApi
from .crypto import Entity, Address

AddressLike = Union[Address, Identity]


def _compute_digest(source) -> Address:
    return Address(sha256_hash(source.encode('ascii')))


class Contract:
    def __init__(self, source: str, owner: AddressLike, nonce: bytes = None):
        self._source = str(source)
        self._digest = _compute_digest(self._source)
        self._owner = Address(owner)
        self._nonce = bytes(urandom(8)) if nonce is None else nonce

        hasher = hashlib.sha256()
        hasher.update(bytes(self._owner))
        hasher.update(self._nonce)

        self._address = Address(hasher.digest())

        # Etch parser for analysing contract
        self._parser = EtchParser(self._source)

        # Generate set of action and query entry points
        entries = self._parser.entry_points(['init', 'action', 'query'])
        self._actions = list(set(entries.get('action', [])))
        self._queries = list(set(entries.get('query', [])))

        init = entries.get('init', [])
        if len(init) > 1:
            raise RuntimeError('Contract may not have more than one @init function, found: {}'.format(', '.join(init)))
        self._init = init[0] if len(init) else None

    @property
    def name(self) -> str:
        return str(self.address)

    def dumps(self):
        return json.dumps(self._to_json_object())

    def dump(self, fp):
        return json.dump(self._to_json_object(), fp)

    @classmethod
    def loads(cls, s):
        return cls._from_json_object(json.loads(s))

    @classmethod
    def load(cls, fp):
        return cls._from_json_object(json.load(fp))

    @property
    def owner(self) -> Address:
        return self._owner

    @property
    def source(self) -> str:
        return self._source

    @property
    def digest(self) -> str:
        return bytes(self._digest).hex()

    @property
    def nonce(self) -> str:
        return base64.b64encode(self._nonce).decode()

    @property
    def nonce_bytes(self) -> bytes:
        return self._nonce

    @property
    def address(self) -> Address:
        return self._address

    @property
    def encoded_source(self) -> str:
        return base64.b64encode(self.source.encode('ascii')).decode()

    def create_as_tx(self, api: LedgerApi, from_address: AddressLike, fee: int,
                     signers: Iterable[Identity]) -> 'Transaction':
        # build the shard mask for the
        shard_mask = self._build_shard_mask(api.server.num_lanes(), self._init)
        tx = ContractTxFactory.create(Address(from_address), self, fee, signers, shard_mask=shard_mask)
        api.set_validity_period(tx)

        return tx

    def create(self, api: LedgerApi, owner: Entity, fee: int):

        # build the shard mask for the
        shard_mask = self._build_shard_mask(api.server.num_lanes(), self._init)
        return api.contracts.create(owner, self, fee, shard_mask=shard_mask)

    def query(self, api: LedgerApi, name: str, **kwargs):
        # TODO(WK): Reinstate without breaking contract-to-contract calls
        # if name not in self._queries:
        #     raise RuntimeError(
        #         '{} is not an valid query name. Valid options are: {}'.format(name, ','.join(list(self._queries))))

        # make the required query on the API
        success, response = api.contracts.query(self.address, name, **kwargs)

        if not success:
            if response is not None and "msg" in response:
                raise RuntimeError('Failed to make requested query: ' + response["msg"])
            else:
                raise RuntimeError('Failed to make requested query with no error message.')

        return response['result']

    def action(self, api: LedgerApi, name: str, fee: int, signers: List[Entity], *args,
               from_address: Address = None):

        # TODO(WK): Reinstate without breaking contract-to-contract calls
        # if name not in self._actions:
        #     raise RuntimeError(
        #         '{} is not an valid action name. Valid options are: {}'.format(name, ','.join(list(self._actions))))

        shard_mask = self._build_shard_mask(api.server.num_lanes(), name)

        return api.contracts.action(self.address, name, fee, signers, *args,
                                    from_address=from_address, shard_mask=shard_mask)

    def _build_shard_mask(self, num_lanes: int, name: Optional[str]) -> BitVector:
        try:
            resource_addresses = [
                'fetch.contract.state.{}'.format(str(self.address)),
            ]

            # only process the init functions resources if this function is actually present
            if name is not None:
                for variable in self._parser.used_globals_to_addresses(name, [self._owner]):
                    resource_addresses.append(ShardMask.state_to_address(str(self.address), variable))

            shard_mask = ShardMask.resources_to_shard_mask(resource_addresses, num_lanes)

        except (UnparsableAddress, UseWildcardShardMask, EtchParserError):
            logging.warning("Couldn't auto-detect used shards, using wildcard shard mask")
            shard_mask = BitVector()

        return shard_mask

    @staticmethod
    def _from_json_object(obj):
        assert obj['version'] == 1

        source = base64.b64decode(obj['source']).decode()
        owner = obj['owner']
        nonce = base64.b64decode(obj['nonce'].encode())

        sc = Contract(
            source,
            owner,
            nonce)

        return sc

    def _to_json_object(self):
        return {
            'version': 1,
            'nonce': self.nonce,
            'owner': None if self._owner is None else str(self._owner),
            'source': self.encoded_source
        }
