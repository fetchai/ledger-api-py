import base64
import hashlib
import json
import logging
from os import urandom
from typing import Union, List

from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Identity
from fetchai.ledger.parser.etch_parser import EtchParser, UnparsableAddress, UseWildcardShardMask
from fetchai.ledger.serialisation.shardmask import ShardMask
from .api import ContractsApi, LedgerApi
from .crypto import Entity, Address

ContractsApiLike = Union[ContractsApi, LedgerApi]
AddressLike = Union[Address, Identity]


def _compute_digest(source) -> Address:
    hash_func = hashlib.sha256()
    hash_func.update(source.encode('ascii'))
    return Address(hash_func.digest())


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
    def name(self):
        return '{}.{}'.format(self.digest.to_hex(), self.address)

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
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, owner):
        self._owner = Address(owner)

    @property
    def source(self):
        return self._source

    @property
    def digest(self):
        return self._digest

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
    def encoded_source(self):
        return base64.b64encode(self.source.encode('ascii')).decode()

    def create(self, api: ContractsApiLike, owner: Entity, fee: int):
        # Set contract owner (required for resource prefix)
        self.owner = owner

        if self._init is None:
            raise RuntimeError("Contract has no initialisation function")

        # Generate resource addresses used by persistent globals
        try:
            resource_addresses = ['fetch.contract.state.{}'.format(self.digest.to_hex())]
            resource_addresses.extend(ShardMask.state_to_address(address, self) for address in
                                      self._parser.used_globals_to_addresses(self._init, [self._owner]))
        except (UnparsableAddress, UseWildcardShardMask):
            logging.warning("Couldn't auto-detect used shards, using wildcard shard mask")
            shard_mask = BitVector()
        else:
            # Generate shard mask from resource addresses
            shard_mask = ShardMask.resources_to_shard_mask(resource_addresses, api.server.num_lanes())

        return self._api(api).create(owner, self, fee, shard_mask=shard_mask)

    def query(self, api: ContractsApiLike, name: str, **kwargs):
        if self._owner is None:
            raise RuntimeError('Contract has no owner, unable to perform any queries. Did you deploy it?')

        if name not in self._queries:
            raise RuntimeError(
                '{} is not an valid query name. Valid options are: {}'.format(name, ','.join(list(self._queries))))

        # make the required query on the API
        success, response = self._api(api).query(self._digest, self.address, name, **kwargs)

        if not success:
            if response is not None and "msg" in response:
                raise RuntimeError('Failed to make requested query: ' + response["msg"])
            else:
                raise RuntimeError('Failed to make requested query with no error message.')

        return response['result']

    def action(self, api: ContractsApiLike, name: str, fee: int, signers: List[Entity], *args):
        if self._owner is None:
            raise RuntimeError('Contract has no owner, unable to perform any actions. Did you deploy it?')

        if name not in self._actions:
            raise RuntimeError(
                '{} is not an valid action name. Valid options are: {}'.format(name, ','.join(list(self._actions))))

        try:
            # Generate resource addresses used by persistent globals
            resource_addresses = [ShardMask.state_to_address(address, self) for address in
                                  self._parser.used_globals_to_addresses(name, list(args))]
        except (UnparsableAddress, UseWildcardShardMask):
            logging.warning("Couldn't auto-detect used shards, using wildcard shard mask")
            shard_mask = BitVector()
        else:
            # Generate shard mask from resource addresses
            shard_mask = ShardMask.resources_to_shard_mask(resource_addresses, api.server.num_lanes())

        return self._api(api).action(self._digest, self.address, name, fee, self.owner, signers, *args,
                                     shard_mask=shard_mask)

    @staticmethod
    def _api(api: ContractsApiLike):
        if isinstance(api, ContractsApi):
            return api
        elif isinstance(api, LedgerApi):
            return api.contracts
        else:
            assert False

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
