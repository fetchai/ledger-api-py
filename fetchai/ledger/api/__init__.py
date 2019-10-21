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

import logging
import time
from datetime import datetime, timedelta
from typing import Sequence, Union

import semver

from fetchai.ledger import __compatible__, IncompatibleLedgerVersion
from fetchai.ledger.api import bootstrap
from fetchai.ledger.api.server import ServerApi
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
        server_version = self.server.version().lstrip('v')
        if server_version.startswith('Unknown version with hash'):
            logging.warning('Using development version')
        elif not all(semver.match(server_version, c) for c in __compatible__):
            raise IncompatibleLedgerVersion("Ledger version running on server is not compatible with this API" +
                                            "\nServer version: {} \nExpected version: {}".format(
                                                server_version, ', '.join(__compatible__)))

    def sync(self, txs: Transactions, timeout=None):
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

        while True:
            # loop through all the remaining digests and poll them creating a set of completed in this round
            remaining_statuses = [self.tx.status(digest) for digest in remaining]

            failed_this_round = [status for status in remaining_statuses if status.failed]
            if failed_this_round:
                failures = ['{}:{}'.format(tx_status.digest_hex, tx_status.status) \
                            for tx_status in failed_this_round]
                raise RuntimeError('Some transactions have failed: {}'.format(', '.join(failures)))

            successful_this_round = [status for status in remaining_statuses if status.successful]
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

    def wait_for_blocks(self, n):
        initial = self.tokens._current_block_number()
        while True:
            time.sleep(1)
            current = self.tokens._current_block_number()
            if current > initial + n:
                break
