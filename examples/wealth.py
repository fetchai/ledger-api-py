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

from fetchai.ledger.api import TokenApi, TransactionApi
from fetchai.ledger.crypto import Identity

HOST = '127.0.0.1'
PORT = 8000


def main():

    # create the APIs
    txs = TransactionApi(HOST, PORT)
    tokens = TokenApi(HOST, PORT)

    # generate a random identity
    identity = Identity()

    print('Balance Before:', tokens.balance(identity.public_key))

    # create and send the transaction to the ledger capturing the tx hash
    tx = tokens.wealth(identity.private_key_bytes, 1000)

    # wait while we poll to see when this transaction has been completed
    prev_status = None
    while True:
        status = txs.status(tx)

        # print the changes in tx status
        if status != prev_status:
            print('Current Status:', status)
            prev_status = status

        # exit the wait loop once the transaction has been executed
        if status == "Executed":
            break

        time.sleep(1)

    # check the balance now
    print('Balance After:', tokens.balance(identity.public_key))


if __name__ == '__main__':
    main()
