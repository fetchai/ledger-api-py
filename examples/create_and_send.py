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

#
# How to send transactions over HTTP using the Python SDK
#

import time

from fetchai.ledger.api import TokenApi, TransactionApi
from fetchai.ledger.crypto import Identity

HOST = '127.0.0.1'
PORT = 8000


def wait_for_tx(txs: TransactionApi, tx: str):
    while True:
        if txs.status(tx) == "Executed":
            break
        else:
        	print('Current Status:', txs.status(tx))
        time.sleep(1)


def main():
    # create the APIs
    txs = TransactionApi(HOST, PORT)
    tokens = TokenApi(HOST, PORT)

    # generate a random identity
    your_identity = Identity()
    other_identity = Identity()
    print('Balance Before:', tokens.balance(your_identity.public_key))
    print (dir(your_identity))

    # create the balance
    print('Submitting wealth creation...')
    wait_for_tx(txs, tokens.wealth(your_identity.private_key_bytes, 1000))
    print('Balance after wealth:', tokens.balance(your_identity.public_key))

    # submit and wait for the transfer to be complete
    print('Submitting transfer...')
    wait_for_tx(txs, tokens.transfer(your_identity.private_key_bytes, other_identity.public_key_bytes, 250))

    print('Balance 1:', tokens.balance(your_identity.public_key))
    print('Balance 2:', tokens.balance(other_identity.public_key))

    print('Balance After:', tokens.balance(your_identity.public_key))


if __name__ == '__main__':
    main()
