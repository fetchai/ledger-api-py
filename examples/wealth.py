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
from fetchai.ledger.crypto import Entity

HOST = '127.0.0.1'
PORT = 8000


def wait_for_tx(txs: TransactionApi, tx: str):
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


def main():

    miner_address = 'yqjE1nCKLYRS3DUeFPmumR4sjQJFRYvKU2KQhdUFKQgkVUr6y'

    # create the APIs
    txs = TransactionApi(HOST, PORT)
    tokens = TokenApi(HOST, PORT)

    # generate a random identity
    entity1 = Entity()
    entity2 = Entity()

    entity1_balance = tokens.balance(entity1)
    entity2_balance = tokens.balance(entity2)
    miner_balance = tokens.balance(miner_address)
    print('Balance @ T==0 -> e1: {} e2: {} miner: {}'.format(entity1_balance, entity2_balance, miner_balance))

    # create and send the transaction to the ledger capturing the tx hash
    tx = tokens.wealth(entity1, 1000, 100)
    wait_for_tx(txs, tx)

    entity1_balance = tokens.balance(entity1)
    entity2_balance = tokens.balance(entity2)
    miner_balance = tokens.balance(miner_address)
    print('Balance @ T==1 -> e1: {} e2: {} miner: {}'.format(entity1_balance, entity2_balance, miner_balance))

    tx = tokens.transfer(entity1, entity2, 500, 100)
    wait_for_tx(txs, tx)

    entity1_balance = tokens.balance(entity1)
    entity2_balance = tokens.balance(entity2)
    miner_balance = tokens.balance(miner_address)
    print('Balance @ T==2 -> e1: {} e2: {} miner: {}'.format(entity1_balance, entity2_balance, miner_balance))


if __name__ == '__main__':
    main()
