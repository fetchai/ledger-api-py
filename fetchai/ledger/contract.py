import json
from typing import Union

from .api import ContractsApi, LedgerApi

ContractsApiLike = Union[ContractsApi, LedgerApi]

import base64
import hashlib
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
    TYPE = None

    def __init__(self, source: str):
        self._source = str(source)
        self._digest = _compute_digest(self._source)

    def dumps(self):
        return json.dumps(self._to_json_object())

    def dump(self, fp):
        return json.dump(self._to_json_object(), fp)

    @property
    def source(self):
        return self._source

    @property
    def digest(self):
        return self._digest

    @property
    def encoded_source(self):
        return base64.b64encode(self.source.encode('ascii')).decode()

    def _to_json_object(self):
        raise NotImplementedError()


class SmartContract(Contract):
    TYPE = 'smart'

    @classmethod
    def loads(cls, s):
        return cls._from_json_object(json.loads(s))

    @classmethod
    def load(cls, fp):
        return cls._from_json_object(json.load(fp))

    def __init__(self, source: str):
        super(SmartContract, self).__init__(source)

        self._owner = None

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
            if response is not None and "msg" in response:
                raise RuntimeError('Failed to make requested query: ' + response["msg"])
            else:
                raise RuntimeError('Failed to make requested query with no error message.')

        return response['result']

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, owner):
        self._owner = Address(owner)

    @staticmethod
    def _api(api: ContractsApiLike):
        if isinstance(api, ContractsApi):
            return api
        elif isinstance(api, LedgerApi):
            return api.contracts
        else:
            assert False

    @classmethod
    def _from_json_object(cls, obj):
        assert obj['version'] == 1
        assert obj['type'] == cls.TYPE

        source = base64.b64decode(obj['source']).decode()

        sc = SmartContract(source)
        owner = obj['owner']
        if owner is not None:
            sc.owner = owner

        return sc

    def _to_json_object(self):
        return {
            'version': 1,
            'type': self.TYPE,
            'owner': None if self._owner is None else str(self._owner),
            'source': self.encoded_source,
        }


class SynergeticContract(Contract):
    TYPE = 'synergetic'

    @classmethod
    def loads(cls, s):
        return cls._from_json_object(json.loads(s))

    @classmethod
    def load(cls, fp):
        return cls._from_json_object(json.load(fp))

    def __init__(self, source: str):
        super(SynergeticContract, self).__init__(source)

    @classmethod
    def _from_json_object(cls, obj):
        assert obj['version'] == 1
        assert obj['type'] == cls.TYPE
        source = base64.b64decode(obj['source']).decode()
        return SynergeticContract(source)

    def _to_json_object(self):
        return {
            'version': 1,
            'type': self.TYPE,
            'source': self.encoded_source,
        }
