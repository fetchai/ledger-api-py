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


def main():
    print('Creating private key...')

    # create our first private key pair
    entity1 = Entity()

    # save the private key to disk
    with open('private.key', 'w') as private_key_file:
        entity1.prompt_dump(private_key_file)

    print('Creating private key...complete')

    # build the ledger API
    api = LedgerApi('127.0.0.1', 8000)

    print('Creating initial balance...')

    # create wealth so that we have the funds to be able to create contracts on the network
    api.sync(api.tokens.wealth(entity1, 10000))

    print('Creating initial balance...complete')


if __name__ == '__main__':
    main()
