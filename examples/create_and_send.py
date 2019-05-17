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

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.crypto import Identity, Entity

HOST = '127.0.0.1'
PORT = 8000


def main():
    # create the APIs
    api = LedgerApi(HOST, PORT)

    # generate a random identity
    your_identity = Entity()
    other_identity = Entity()
    print('Balance Before:', api.tokens.balance(your_identity))

    # create the balance
    print('Submitting wealth creation...')
    api.sync(api.tokens.wealth(your_identity, 1000))
    print('Balance after wealth:', api.tokens.balance(your_identity))

    # submit and wait for the transfer to be complete
    print('Submitting transfer...')
    api.sync(api.tokens.transfer(your_identity, other_identity, 250, 20))

    print('Balance 1:', api.tokens.balance(your_identity))
    print('Balance 2:', api.tokens.balance(other_identity))


if __name__ == '__main__':
    main()
