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

import requests
import json


def format_contract_url(host, port, *args):
    """
    Constructs a URL based on specified contract prefix and endpoint

    :param str host: The target host
    :param int port: The target port
    :param str prefix: The dot separated prefix for the contract
    :param str endpoint: The dot separated name for the contract endpoint
    :return: The formatted URL
    """
    if args is None:
        canonical_name = endpoint
    else:
        canonical_name = '.'.join([*args])

    return 'http://{}:{}/api/contract/'.format(host, port) + canonical_name.replace('.', '/')


def submit_json_transaction(host, port, tx_data, session=None):
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

    def _post_json(self, endpoint, data=None):
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
        url = format_contract_url(self.host, self.port, self.API_PREFIX, endpoint)

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

    def _post_tx(self, transaction, endpoint):
        """
        Submits a transaction to the a ledger endpoint

        :param str transaction: The JSON encoded contract contents
        :param str endpoint: The target endpoint of the contract
        :return: True if the transaction was successfully submitted
        """

        headers = {
            'content-type': 'application/vnd+fetch.transaction+json',
        }

        # format the URL
        url = format_contract_url(self.host, self.port, self.API_PREFIX, endpoint)

        # make the request
        r = self._session.post(url, data=transaction, headers=headers)
        success = 200 <= r.status_code < 300

        if not success:
            raise ApiError(
                    'Unable to fulfil transaction request {}.{}. Status Code {} Text: {}'.format(self.API_PREFIX, endpoint,
                                                                                    r.status_code, r.text))

    def _post_tx_speculative(self, transaction, endpoint):
        """
        Submits a speculative transaction to the ledger endpoint. That is,
        submit the transaction and have the node run it to determine side effects.
        Basically identical to a normal submission except the server return code
        will contain your print statements

        :param str transaction: The JSON encoded contract contents
        :param str endpoint: The target endpoint of the contract
        :return: True if the transaction was successfully submitted
        """

        headers = {
            'content-type': 'application/vnd+fetch.transaction+json',
        }

        # format the URL
        url = format_contract_url(self.host, self.port, 'speculative', self.API_PREFIX, endpoint)

        print("Making speculative call to: " + url)

        # make the request
        r = self._session.post(url, data=transaction, headers=headers)
        success = 200 <= r.status_code < 300

        if not success:
            raise ApiError(
                    'Unable to fulfil transaction request {}.{}. Status Code {} Text: {}'.format(self.API_PREFIX, endpoint,
                                                                                    r.status_code, r.text))
        return r;
