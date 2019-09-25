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

import time
from datetime import datetime, timedelta
from typing import Sequence, Union

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


class LedgerApi:
    def __init__(self, host, port):
        self.tokens = TokenApi(host, port)
        self.contracts = ContractsApi(host, port)
        self.tx = TransactionApi(host, port)

    def sync(self, txs: Transactions, timeout=None):
        timeout = int(timeout or 120)
        # given the inputs make sure that we correctly for the input set of values
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
            remaining -= set([digest for digest in remaining if self._poll(digest)])

            # once we have completed all the outstanding transactions
            if len(remaining) == 0:
                break

            # time out mode
            delta_time = datetime.now() - start
            if delta_time >= limit:
                raise RuntimeError('Timeout waiting for txs: {}'.format(', '.join(list(remaining))))

            time.sleep(1)

    def _poll(self, digest):
        return self.tx.status(digest) in ('Executed', 'Submitted')

    def wait_for_blocks(self, n):
        initial = self.tokens._current_block_number()
        while True:
            time.sleep(1)
            current = self.tokens._current_block_number()
            if current > initial + n:
                break
