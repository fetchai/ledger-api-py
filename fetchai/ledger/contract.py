import base64
import hashlib
import json
import re
from typing import Union, List

from .api import ContractsApi, LedgerApi
from .crypto import Entity, Address

ContractsApiLike = Union[ContractsApi, LedgerApi]


def _compute_digest(source) -> Address:
    hash_func = hashlib.sha256()
    hash_func.update(source.encode('ascii'))
    return Address(hash_func.digest())


class Contract:
    def __init__(self, source: str):
        self._source = str(source)
        self._digest = _compute_digest(self._source)
        self._owner = None

        # Quick and easy method to inspecting the contract source and generating a set of action and query names. To
        # be replaced in the future with a more fault tolerant approach
        ugly = ' '.join(map(lambda x: x.strip(), source.splitlines()))
        self._actions = set(re.findall(r'@action function (\w+)\(', ugly))
        self._queries = set(re.findall(r'@query function (\w+)\(', ugly))

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
    def encoded_source(self):
        return base64.b64encode(self.source.encode('ascii')).decode()

    def query(self, api: ContractsApiLike, name: str, **kwargs):
        if self._owner is None:
            raise RuntimeError('Contract has no owner, unable to perform any queries. Did you deploy it?')

        if name not in self._queries:
            raise RuntimeError(
                '{} is not an valid query name. Valid options are: {}'.format(name, ','.join(list(self._queries))))

        # make the required query on the API
        success, response = self._api(api).query(self._digest, self._owner, name, **kwargs)

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

        return self._api(api).action(self._digest, self._owner, name, fee, signers, *args)

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
        sc = Contract(source)

        owner = obj['owner']
        if owner is not None:
            sc.owner = owner

        return sc

    def _to_json_object(self):
        return {
            'version': 1,
            'owner': None if self._owner is None else str(self._owner),
            'source': self.encoded_source
        }
