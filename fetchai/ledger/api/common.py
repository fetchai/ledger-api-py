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
import json
from typing import Optional

import requests


def format_contract_url(host: str, port: int, prefix: Optional[str], endpoint: Optional[str]):
    """
    Constructs a URL based on specified contract prefix and endpoint

    :param host: The target host
    :param port: The target port
    :param prefix: The dot separated prefix for the contract
    :param endpoint: The dot separated name for the contract endpoint
    :return: The formatted URL
    """

    if endpoint is None:
        url = 'http://{}:{}/api/contract/submit'.format(host, port)

    else:
        if prefix is None:
            canonical_name = endpoint
        else:
            canonical_name = '.'.join([prefix, endpoint])

        url = 'http://{}:{}/api/contract/'.format(host, port) + canonical_name.replace('.', '/')

    return url


def submit_json_transaction(host: str, port: int, tx_data, session=None):
    """
    Submit a JSON transaction to the target onde

    :param host: The host to target ledger instance
    :param port: The port to target ledger instance
    :param tx_data: The object that will be json encoded
    :param session: Optional session object to be passed to the
    :return: True is the request was successful, otherwise False
    """
    if session is None:
        session = requests.session()

    # define the URL to be used
    uri = format_contract_url(host, port, None, 'submit')

    headers = {
        'content-type': 'application/vnd+fetch.transaction+json',
    }

    # make the request
    r = session.post(uri, json=tx_data, headers=headers)

    # check the status code
    return 200 <= r.status_code < 300


def submit_native_transactions(host, port, native_tx, session=None):
    raise NotImplementedError('This function has not been implemented')


class ApiError(RuntimeError):
    pass


class ApiEndpoint(object):
    API_PREFIX = None

    def __init__(self, host, port):
        self._host = str(host)
        self._port = int(port)
        self._session = requests.session()

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
        url = format_contract_url(self.host, self.port, prefix or self.API_PREFIX, endpoint)

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

        return False, None

    def _post_tx_json(self, tx_data: bytes, endpoint: Optional[str]):
        """
        Submits a transaction to the a ledger endpoint

        :param tx_data: The binary encoded transaction
        :param endpoint: The target endpoint of the contract
        :return: The digest of the submitted transaction
        """

        headers = {
            'content-type': 'application/vnd+fetch.transaction+json',
        }

        tx_payload = dict(ver="1.2", data=base64.b64encode(tx_data).decode())

        # format the URL
        url = format_contract_url(self.host, self.port, self.API_PREFIX, endpoint)

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
