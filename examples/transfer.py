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

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.crypto import Entity

HOST = '127.0.0.1'
PORT = 8000


def main():
    # create the APIs
    api = LedgerApi(HOST, PORT)

    # generate identities from hex private keys,
    identity1 = Entity.from_hex('6e8339a0c6d51fc58b4365bf2ce18ff2698d2b8c40bb13fcef7e1ba05df18e4b')
    identity2 = Entity.from_hex('e833c747ee0aeae29e6823e7c825d3001638bc30ffe50363f8adf2693c3286f8')

    print('Balance 1 Before:', api.tokens.balance(identity1))
    print('Balance 2 Before:', api.tokens.balance(identity2))

    # submit and wait for the transfer to be complete
    print('Submitting transfer...')
    api.sync(api.tokens.transfer(identity1, identity2, 250, 20))

    print('Balance 1:', api.tokens.balance(identity1))
    print('Balance 2:', api.tokens.balance(identity2))


if __name__ == '__main__':
    main()
