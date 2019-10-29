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
from contextlib import contextmanager
from typing import List

from fetchai.ledger.api import LedgerApi, TokenApi
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity, Address

CONTRACT_TEXT = """
persistent sharded balance_state : UInt64;

@init
function setup(owner : Address)
  use balance_state[owner];

  balance_state.set(owner, 1000000u64);
endfunction

@action
function transfer(from: Address, to: Address, amount: UInt64)
  use balance_state[from, to];

  // Check if the sender has enough balance to proceed
  if (balance_state.get(from) >= amount)
    // update the account balances
    balance_state.set(from, balance_state.get(from) - amount);
    balance_state.set(to, balance_state.get(to, 0u64) + amount);
  endif

endfunction

@query
function balance(address: Address) : UInt64
  use balance_state[address];

  return balance_state.get(address, 0u64);
endfunction

"""


def print_address_balances(api: LedgerApi, contract: Contract, addresses: List[Address]):
    for idx, address in enumerate(addresses):
        print('Address{}: {:<6d} bFET {:<10d} TOK'.format(idx, api.tokens.balance(address),
                                                          contract.query(api, 'balance', address=address)))
    print()


@contextmanager
def track_cost(api: TokenApi, entity: Entity, message: str):
    """
    Context manager for recording the change in balance over a set of actions
    Will be inaccurate if other factors change an account balance
    """
    if isinstance(entity, Entity):
        entity = Address(entity)
    elif not isinstance(entity, Address):
        raise TypeError("Expecting Entity or Address")

    balance_before = api.balance(entity)
    yield

    if not message:
        message = "Actions cost: "

    print(message + "{} TOK".format(api.balance(entity) - balance_before))


def main():
    # create our first private key pair
    entity1 = Entity()
    address1 = Address(entity1)

    # create a second private key pair
    entity2 = Entity()
    address2 = Address(entity2)

    # build the ledger API
    api = LedgerApi('127.0.0.1', 8000)

    # create wealth so that we have the funds to be able to create contracts on the network
    api.sync(api.tokens.wealth(entity1, 10000))

    # create the smart contract
    contract = Contract(CONTRACT_TEXT, entity1)

    with track_cost(api.tokens, entity1, "Cost of creation: "):
        api.sync(contract.create(api, entity1, 4000))

    # print the current status of all the tokens
    print('-- BEFORE --')
    print_address_balances(api, contract, [address1, address2])

    # transfer from one to the other using our newly deployed contract
    tok_transfer_amount = 200
    fet_tx_fee = 160
    with track_cost(api.tokens, entity1, "Cost of transfer: "):
        api.sync(contract.action(api, 'transfer', fet_tx_fee, [entity1], address1, address2, tok_transfer_amount))

    print('-- AFTER --')
    print_address_balances(api, contract, [address1, address2])


if __name__ == '__main__':
    main()
