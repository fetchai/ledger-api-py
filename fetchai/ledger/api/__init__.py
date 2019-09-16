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
from .synergetic import SynergeticApi
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
    """This class encapsulates the top level functionality of the Ledger API.
    """
    def __init__(self, host, port):
        """Constructor method that creates the specific APIs.

        :param host: the Ledger API url.
        :param port: the Ledger API port.
        :param tokens: an object reference to the TokenApi running on host and port.
        :param contracts: an object reference to the ContractsApi running on host and port.
        :param tx: an object reference to the TransactionApi running on host and port.
        :param synergetic: an object reference to the SynergeticApi running on host and port.
        """
        self.tokens = TokenApi(host, port)
        self.contracts = ContractsApi(host, port)
        self.tx = TransactionApi(host, port)
        self.synergetic = SynergeticApi(host, port)

    def sync(self, txs: Transactions):
        """This function ensures all asynchronous transactions sent via a contract function are verified before code moves forward.

        :param txs: the transactions sent to the contract function.
        """

        # ensure inputs to sync are dealt with correctly
        if isinstance(txs, str):
            remaining = {txs}
        elif _iterable(txs):
            remaining = set(txs)
        else:
            raise TypeError('Unknown argument type')

        # give a Transaction 2 minutes to verify
        limit = timedelta(minutes=2)
        start = datetime.now()
        while True:

            # loop through all the remaining Transaction digests and poll them to see if they are completed.
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
        """This function checks the Transaction digest state. All contract transactions should complete and return an "Executed" state.
        However, Synergetic contract transactions with submit data should complete and return with a "Submitted" state.

        :param digest: the transaction digests sent to sync.
        """
        return self.tx.status(digest) in ('Executed', 'Submitted')
