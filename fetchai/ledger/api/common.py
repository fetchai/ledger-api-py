# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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

import base64
import functools
import json
import warnings
from typing import Optional, Union, Iterable

import msgpack
import requests

from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Address, Identity
from fetchai.ledger.serialisation import transaction
from fetchai.ledger.transaction import Transaction

DEFAULT_BLOCK_VALIDITY_PERIOD = 100

AddressLike = Union[Address, Identity]


def unstable(func):
    """
    Function Decorator to signal which parts of the API are expected to be unstable
    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn(
            "Call to unstable API. It is expect that future API updates are possible {}.".format(func.__name__),
            category=UserWarning, stacklevel=2)
        return func(*args, **kwargs)

    return new_func


def format_contract_url(host: str, port: int, prefix: Optional[str], endpoint: Optional[str], protocol: str = None):
    """
    Constructs a URL based on specified contract prefix and endpoint

    :param host: The target host
    :param port: The target port
    :param prefix: The dot separated prefix for the contract
    :param endpoint: The dot separated name for the contract endpoint
    :param protocol: Transfer protocol, either 'http' or 'https'
    :return: The formatted URL
    """
    # Default to http protocol
    protocol = protocol or 'http'

    if endpoint is None:
        url = '{}://{}:{}/api/contract/submit'.format(protocol, host, port)

    else:
        if prefix is None:
            canonical_name = endpoint
        else:
            canonical_name = '.'.join([prefix, endpoint])

        url = '{}://{}:{}/api/contract/{}'.format(
            protocol,
            host,
            port,
            canonical_name.replace('.', '/'))

    return url


def submit_json_transaction(host: str, port: int, tx_data, session=None, protocol: str = None, endpoint: str = None):
    """
    Submit a JSON transaction to the target onde

    :param host: The host to target ledger instance
    :param port: The port to target ledger instance
    :param tx_data: The object that will be json encoded
    :param session: Optional session object to be passed to the
    :param protocol: Transfer protocol, either 'http' or 'https'
    :return: True is the request was successful, otherwise False
    """
    if session is None:
        session = requests.session()

    # define the URL to be used
    uri = format_contract_url(host, port, None, endpoint=endpoint, protocol=protocol)

    headers = {
        'content-type': 'application/vnd+fetch.transaction+json',
    }

    # make the request
    r = session.post(uri, json=tx_data, headers=headers)
    success = 200 <= r.status_code < 300

    # The following code is to get the transaction id
    if not success:
        raise ApiError(
            'Unable to fulfill transaction request {}.{}. Status Code {}'.format(uri, endpoint,
                                                                                 r.status_code))

    # parse the response
    response = r.json()

    # attempt to extract out the submitting transaction hash
    tx_list = response.get('txs', [])
    if len(tx_list):
        return tx_list[0]


def submit_native_transactions(host, port, native_tx, session=None):
    raise NotImplementedError('This function has not been implemented')


class ApiError(RuntimeError):
    pass


class ApiEndpoint(object):
    API_PREFIX = None

    def __init__(self, host, port):
        if '://' in host:
            protocol, host = host.split('://')
        else:
            protocol = 'http'

        self._protocol = protocol
        self._host = str(host)
        self._port = int(port)
        self._session = requests.session()

    @property
    def protocol(self):
        return self._protocol

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @classmethod
    def _format_chain_code(cls, endpoint):
        return cls.API_PREFIX + '.' + endpoint

    @classmethod
    def _encode_json(cls, obj):
        return json.dumps(obj).encode('ascii')

    def _create_skeleton_tx(self, fee: int, validity_period: Optional[int] = None):
        # build up the basic transaction information
        tx = Transaction()
        tx.charge_rate = 1
        tx.charge_limit = fee
        self._set_validity_period(tx, validity_period)
        return tx

    def _set_validity_period(self, tx: Transaction, validity_period: Optional[int] = None):
        validity_period = validity_period or DEFAULT_BLOCK_VALIDITY_PERIOD

        # query what the current block number is on the node
        current_block = self.current_block_number()

        # populate both the valid from and valid until
        tx.valid_from = current_block
        tx.valid_until = current_block + validity_period
        return tx.valid_until

    def current_block_number(self):
        success, data = self._get_json('status/chain', size=1)
        if success:
            return data['chain'][0]['blockNumber']

        raise RuntimeError('Unable to query current block number')

    def _get_json(self, path, **kwargs):
        args = dict(**kwargs)
        params = args if len(args) > 0 else None
        url = '{}://{}:{}/api/{}'.format(self._protocol, self._host, self._port, path)

        # make the request
        raw_response = self._session.get(url, params=params)

        # check the status code
        if 200 <= raw_response.status_code < 300:
            response = json.loads(raw_response.text)
            return True, response

        return False, None

    def _post_json(self, endpoint, data=None, prefix=None):
        """
        Submits a query request to a ledger endpoint

        :param str endpoint: The target endpoint of the contract
        :param data: JSON serialisable object containing request parameters
        :return:
        """

        # generate a simple
        if data is None:
            data = dict()

        # strip leading '/' if needed
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]

        # format and make the request
        url = format_contract_url(self.host, self.port, prefix or self.API_PREFIX, endpoint, protocol=self.protocol)

        # define the request headers
        headers = {
            'content-type': 'application/json',
        }

        # make the request
        raw_response = self._session.post(url, json=data, headers=headers)

        # check the status code
        if 200 <= raw_response.status_code < 300:
            response = json.loads(raw_response.text)
            return True, response

        # Allow for additional data to be transferred
        response = None
        try:
            response = json.loads(raw_response.text)
        except:
            pass

        return False, response

    def _post_tx_json(self, tx_data: bytes, endpoint: Optional[str]):
        """
        Submits a transaction to the a ledger endpoint

        :param tx_data: The binary encoded transaction
        :param endpoint: The target endpoint of the contract
        :return: The hexadecimal digest of the submitted transaction
        """

        headers = {
            'content-type': 'application/vnd+fetch.transaction+json',
        }

        tx_payload = dict(ver="1.2", data=base64.b64encode(tx_data).decode())

        # format the URL
        url = format_contract_url(self.host, self.port, self.API_PREFIX, endpoint, protocol=self.protocol)

        # make the request
        r = self._session.post(url, json=tx_payload, headers=headers)
        success = 200 <= r.status_code < 300

        if not success:
            raise ApiError(
                'Unable to fulfil transaction request {}.{}. Status Code {}'.format(self.API_PREFIX, endpoint,
                                                                                    r.status_code))

        # parse the response
        response = r.json()

        # attempt to extract out the submitting transaction hash
        tx_list = response.get('txs', [])
        if len(tx_list):
            return tx_list[0]

    def submit_signed_tx(self, tx: Transaction):
        """
        Appends signatures to a transaction and submits it, returning the transaction digest
        :param tx: A pre-assembled transaction
        :param signatures: A dict of signers signatures
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """
        # encode transaction and append signatures
        encoded_tx = transaction.encode_transaction(tx)

        # submit and return digest
        return self._post_tx_json(encoded_tx, None)


class TransactionFactory:
    API_PREFIX = None

    @classmethod
    def _create_skeleton_tx(cls, fee: int) -> Transaction:
        # build up the basic transaction information
        tx = Transaction()
        tx.charge_rate = 1
        tx.charge_limit = fee
        return tx

    @classmethod
    def _create_chain_code_action_tx(cls, fee: int, from_address: AddressLike, action: str,
                                     signatories: Iterable[Identity],
                                     shard_mask: BitVector) -> Transaction:
        tx = cls._create_skeleton_tx(fee)
        tx.from_address = Address(from_address)
        tx.target_chain_code(cls.API_PREFIX, shard_mask)
        tx.action = action
        for ident in signatories:
            tx.add_signer(ident)

        return tx

    @classmethod
    def _create_smart_contract_action_tx(cls, fee: int, from_address: AddressLike, contract_address: AddressLike,
                                         action: str, signatories: Iterable[Identity],
                                         shard_mask: BitVector) -> Transaction:
        tx = cls._create_skeleton_tx(fee)
        tx.from_address = Address(from_address)
        tx.target_contract(Address(contract_address), shard_mask)
        tx.action = str(action)
        for ident in signatories:
            tx.add_signer(ident)

        return tx

    @classmethod
    def _encode_json(cls, obj):
        return json.dumps(obj).encode('ascii')

    @classmethod
    def _encode_msgpack_payload(cls, *args):
        items = []
        for value in args:
            if cls._is_primitive(value):
                items.append(value)
            elif isinstance(value, Address):
                items.append(msgpack.ExtType(77, bytes(value)))
            else:
                raise RuntimeError('Unknown item to pack: ' + value.__class__.__name__)
        return msgpack.packb(items)

    @staticmethod
    def _is_primitive(value):
        for type in (bool, int, float, str):
            if isinstance(value, type):
                return True
        return False
