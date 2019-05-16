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

from .common import ApiEndpoint, ApiError, submit_json_transaction
from .contracts import ContractsApi
from .token import TokenApi
from .tx import TransactionApi


class LedgerApi:
    def __init__(self, host, port):
        self.tokens = TokenApi(host, port)
        self.contracts = ContractsApi(host, port)
        self.tx = TransactionApi(host, port)

    def sync(self, tx):
        limit = timedelta(minutes=2)
        start = datetime.now()
        while True:

            # normal exit mode
            status = self.tx.status(tx)
            if status == "Executed":
                break

            # time out mode
            delta_time = datetime.now() - start
            if delta_time >= limit:
                raise RuntimeError('Timeout waiting for ledger operation state: ' + str(status))

            time.sleep(1)
