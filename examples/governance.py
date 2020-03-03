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
from getpass import getpass

from pocketbook.key_store import KeyStore

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.crypto import Address


def get_miner_private_key(pocketbook_key_name: str, password: str = None):
    password = getpass(prompt='Password for key {}: '.format(pocketbook_key_name)) \
        if password is None \
        else password

    ks = KeyStore()

    return ks.load_key(
        pocketbook_key_name,
        password)


def main():
    entity1 = get_miner_private_key('my_miner_wallet')
    address1 = Address(entity1)
    api = LedgerApi('127.0.0.1', 9001)

    proposal = {
        'version': 0,
        'accept_by': 1000,
        'data': {
            'charge_multiplier': 42
        }
    }

    propose_tx = api.governance.propose(address1, 10000, [entity1], proposal)
    api.sync(propose_tx)

    accept_tx = api.governance.accept(address1, 10000, [entity1], proposal)
    api.sync(accept_tx)


if __name__ == '__main__':
    main()
