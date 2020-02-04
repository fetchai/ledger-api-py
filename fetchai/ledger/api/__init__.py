# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

import logging
import re
import time
from datetime import datetime, timedelta
from typing import Sequence, Union, Optional

import semver

from fetchai.ledger import __compatible__, IncompatibleLedgerVersion
from fetchai.ledger.api import bootstrap
from fetchai.ledger.api.server import ServerApi
from fetchai.ledger.transaction import Transaction
from .common import ApiEndpoint, ApiError, submit_json_transaction
from .contracts import ContractsApi
from .token import TokenApi
from .tx import TransactionApi

Transactions = Union[str, Sequence[str]]


def _iterable(value):
    try:
        _ = iter(value)
        return True
    except TypeError:
        pass

    return False


def _get_or_set_default_time(d, key, default):
    """
    Dictionary helper. If the key is not in the d dictionary or the value is set to -1 it will set the key to default
     and return default otherwise returns the value from d.
    :param d: dictionary
    :param key: key we are interested in
    :param default: the default value in case the key is not in d or value -1
    :return: value
    """
    if key in d and d[key] != -1:
        return d[key]
    d[key] = default
    return default


def _pre_process_version(reported_version):
    server_version = reported_version.lstrip('v')

    # remove trailing git version if present
    match = re.match(r'^(\d+\.\d+\.\d+)-(alpha|beta|rc)(\d+)-\d+-(g[a-f0-9]+)$', str(server_version))
    if match is not None:
        server_version = '{}-{}.{}+{}'.format(match.group(1), match.group(2), match.group(3), match.group(4))

    match = re.match(r'^(\d+\.\d+\.\d+)-(alpha|beta|rc)(\d+)$', str(server_version))
    if match is not None:
        server_version = '{}-{}.{}'.format(match.group(1), match.group(2), match.group(3))

    return server_version


def check_version_compatibility(reported_version, compatible_versions):
    server_version = _pre_process_version(reported_version)
    if server_version.startswith('Unknown version with hash'):
        logging.warning('Using development version')
    elif not all(semver.match(server_version, c) for c in compatible_versions):
        raise IncompatibleLedgerVersion("Ledger version running on server is not compatible with this API" +
                                        "\nServer version: {} \nExpected version: {}".format(
                                            server_version, ', '.join(compatible_versions)))


class LedgerApi:
    def __init__(self, host=None, port=None, network=None):
        if network:
            assert not host and not port, 'Specify either a server name, or a host & port'
            host, port = bootstrap.server_from_name(network)
        else:
            assert host and port, "Must specify either a server name, or a host & port"

        self.tokens = TokenApi(host, port)
        self.contracts = ContractsApi(host, port)
        self.tx = TransactionApi(host, port)
        self.server = ServerApi(host, port)

        # Check that ledger version is compatible with API version
        check_version_compatibility(self.server.version(), __compatible__)

    def sync(self, txs: Transactions, timeout: Optional[int] = None, hold_state_sec: int = 0,
             extend_success_status: Optional[Sequence[str]] = None):
        """
        Waits till the transaction list is executed
        :param txs: list of transactions
        :param timeout: max execution time in seconds, default is 120
        :param hold_state_sec: this variable if set will only mark a transaction as executed if the success state is kept for the specified duration
        :param extend_success_status: by default only "Success" is the status indicator, but in some cases other indicators are possible as well
        :return:
        """
        extend_success_status = set(extend_success_status or [])
        timeout = int(timeout or 120)
        # given the inputs make sure that we correctly for the input set of values
        finished = []
        if isinstance(txs, str):
            remaining = {txs}
        elif _iterable(txs):
            remaining = set(txs)
        else:
            raise TypeError('Unknown argument type')

        limit = timedelta(seconds=timeout)
        start = datetime.now()

        hold_state = timedelta(seconds=hold_state_sec)
        hold_times = {}

        while True:
            # loop through all the remaining digests and poll them creating a set of completed in this round
            remaining_statuses = [self.tx.status(digest) for digest in remaining]

            failed_this_round = [status for status in remaining_statuses if status.failed]
            if failed_this_round:
                failures = ['{}:{}'.format(tx_status.digest_hex, tx_status.status) \
                            for tx_status in failed_this_round]
                raise RuntimeError('Some transactions have failed: {}'.format(', '.join(failures)))
            now = datetime.now()
            # Detect transactions with a successful status
            successful_this_round = [status for status in remaining_statuses if
                                     status.successful or status.status in extend_success_status]
            # Filter out transactions which revert to a non-successful state before hold_time elapses
            successful_this_round = [status for status in successful_this_round if
                                     (now - _get_or_set_default_time(hold_times, status.digest_hex, now)) >= hold_state]
            # Reset hold time for transactions which leave a successful state
            hold_times.update({status.digest_hex: -1 for status in remaining_statuses if status.non_terminal})
            finished += successful_this_round

            completed_digests = set([status.digest_hex for status in successful_this_round])
            remaining -= completed_digests

            # once we have completed all the outstanding transactions
            if len(remaining) == 0:
                return finished

            # time out mode
            delta_time = datetime.now() - start
            if delta_time >= limit:
                raise RuntimeError('Timeout waiting for txs: {}'.format(', '.join(list(remaining))))

            time.sleep(1)

    def submit_signed_tx(self, tx: Transaction):
        if not tx.is_valid():
            raise RuntimeError('Signed transaction failed validation checks')

        return self.tokens.submit_signed_tx(tx)

    def set_validity_period(self, tx: Transaction, period: Optional[int] = None):
        self.tokens._set_validity_period(tx, period)

    def wait_for_blocks(self, n):
        initial = self.tokens.current_block_number()
        while True:
            time.sleep(1)
            current = self.tokens.current_block_number()
            if current > initial + n:
                break
