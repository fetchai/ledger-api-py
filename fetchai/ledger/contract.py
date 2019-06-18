import base64
import hashlib
import json
import re
from typing import Union, List

from .api import ContractsApi, LedgerApi
from .crypto import Entity, Address

ContractsApiLike = Union[ContractsApi, LedgerApi]


class SmartContract:

    @classmethod
    def loads(cls, s):
        return cls._from_json_object(json.loads(s))

    @classmethod
    def load(cls, fp):
        return cls._from_json_object(json.load(fp))

    def __init__(self, source: str):
        self._owner = None
        self._source = str(source)
        self._digest = self._compute_digest()

        # Quick and easy method to inspecting the contract source and generating a set of action and query names. To
        # be replaced in the future with a more fault tolerant approach
        ugly = ' '.join(map(lambda x: x.strip(), source.splitlines()))
        self._actions = set(re.findall(r'@action function (\w+)\(', ugly))
        self._queries = set(re.findall(r'@query function (\w+)\(', ugly))

    def action(self, api: ContractsApiLike, name: str, fee: int, signers: List[Entity], *args):
        if self._owner is None:
            raise RuntimeError('Contract has no owner, unable to perform any actions. Did you deploy it?')

        if name not in self._actions:
            raise RuntimeError(
                '{} is not an valid action name. Valid options are: {}'.format(name, ','.join(list(self._actions))))

        return self._api(api).action(self._digest, self._owner, name, fee, signers, *args)

    def query(self, api: ContractsApiLike, name: str, **kwargs):

        if self._owner is None:
            raise RuntimeError('Contract has no owner, unable to perform any queries. Did you deploy it?')

        if name not in self._queries:
            raise RuntimeError(
                '{} is not an valid query name. Valid options are: {}'.format(name, ','.join(list(self._queries))))

        # make the required query on the API
        success, response = self._api(api).query(self._digest, self._owner, name, **kwargs)

        if not success:
            raise RuntimeError('Failed to make requested query')

        return response['result']

    def dumps(self):
        return json.dumps(self._to_json_object())

    def dump(self, fp):
        return json.dump(self._to_json_object(), fp)

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
    def encoded_source(self):
        return base64.b64encode(self.source.encode('ascii')).decode()

    @property
    def digest(self):
        return self._digest

    def _compute_digest(self):
        hash_func = hashlib.sha256()
        hash_func.update(self._source.encode('ascii'))
        return Address(hash_func.digest())

    @staticmethod
    def _api(api: ContractsApiLike):
        if isinstance(api, ContractsApi):
            return api
        elif isinstance(api, LedgerApi):
            return api.contracts
        else:
            assert False

    def _to_json_object(self):
        return {
            'owner': None if self._owner is None else str(self._owner),
            'source': self.encoded_source,
        }

    @classmethod
    def _from_json_object(self, obj):
        source = base64.b64decode(obj['source']).decode()

        sc = SmartContract(source)
        owner = obj['owner']
        if owner is not None:
            sc.owner = owner

        return sc
