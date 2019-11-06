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
from typing import List

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity, Address


def print_address_balances(api: LedgerApi, contract: Contract, addresses: List[Address]):
    for idx, address in enumerate(addresses):
        print('Address{}: {:<6d} bFET {:<10d} TOK'.format(idx, api.tokens.balance(address),
                                                          contract.query(api, 'balance', address=Address(address))))
    print()


def main():
    # load up the previously created private key
    with open('private.key', 'r') as private_key_file:
        entity1 = Entity.prompt_load(private_key_file)

    # load up the deployed contract
    with open('sample.contract', 'r') as contract_file:
        contract = Contract.load(contract_file)

    # for the purposes of this example create a second private key pair to transfer funds to
    entity2 = Entity()

    # build the ledger API
    api = LedgerApi('127.0.0.1', 8000)

    # print the current status of all the tokens
    print('-- BEFORE --')
    print_address_balances(api, contract, [entity1, entity2])

    # transfer from one to the other using our newly deployed contract
    tok_transfer_amount = 200
    fet_tx_fee = 40
    api.sync(contract.action(api, 'transfer', fet_tx_fee, [entity1], Address(entity1), Address(entity2),
                             tok_transfer_amount))

    print('-- AFTER --')
    print_address_balances(api, contract, [entity1, entity2])


if __name__ == '__main__':
    main()
