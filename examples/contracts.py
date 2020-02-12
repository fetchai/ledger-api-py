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
persistent sharded balance_ : UInt64;
persistent supply_ : UInt64;

@init
function init(owner: Address)
    use supply_;
    use balance_[owner];

    supply_.set(92817u64);
    balance_.set(owner, 92817u64);
endfunction

@query
function totalSupply(): UInt64
    use supply_;

    return supply_.get();
endfunction

@query
function balanceOf(address: Address) : UInt64
    use balance_[address];

    return balance_.get(address, 0u64);
endfunction

@action
function transfer(from: Address, to: Address, value: UInt64) : Int64
    use balance_[from, to];

    if(!from.signedTx())
      return 1i64;
    endif

    var from_balance = balance_.get(from, 0u64);
    var to_balance = balance_.get(to, 0u64);

    if(from_balance < value)
      return 1i64;
    endif

    var u_from = from_balance - value;
    var u_to = to_balance + value;

    balance_.set(from, u_from);
    balance_.set(to, u_to);

    return 0i64;
endfunction

"""


def print_address_balances(api: LedgerApi, contract: Contract, addresses: List[Address]):
    for idx, address in enumerate(addresses):
        print('Address{}: {:<6d} bFET {:<10d} TOK'.format(idx, api.tokens.balance(address),
                                                          contract.query(api, 'balanceOf', address=address)))
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
    # In examples we use addresses which already have funds
    entity1 = Entity.from_hex('6e8339a0c6d51fc58b4365bf2ce18ff2698d2b8c40bb13fcef7e1ba05df18e4b')
    entity2 = Entity.from_hex('e833c747ee0aeae29e6823e7c825d3001638bc30ffe50363f8adf2693c3286f8')

    address1 = Address(entity1)

    # create a second private key pair
    address2 = Address(entity2)

    # build the ledger API
    api = LedgerApi('127.0.0.1', 8000)

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
        api.sync(contract.action(api, 'transfer', fet_tx_fee, entity1, address1, address2, tok_transfer_amount))

    print('-- AFTER --')
    print_address_balances(api, contract, [address1, address2])


if __name__ == '__main__':
    main()
