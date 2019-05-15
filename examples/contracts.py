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
from fetchai.ledger.contract import SmartContract
from fetchai.ledger.crypto import Entity, Address

CONTRACT_TEXT = """
@init
function setup(owner : Address)
  var owner_balance = State<UInt64>(owner, 0u64);
  owner_balance.set(1000000u64);
endfunction

@action
function transfer(from: Address, to: Address, amount: UInt64)

  // define the accounts
  var from_account = State<UInt64>(from, 0u64);
  var to_account = State<UInt64>(to, 0u64); // if new sets to 0u

  // Check if the sender has enough balance to proceed
  if (from_account.get() >= amount)
  
    // update the account balances
    from_account.set(from_account.get() - amount);
    to_account.set(to_account.get() + amount);
  endif

endfunction

@query
function balance(address: Address) : UInt64
    var account = State<UInt64>(address, 0u64);
    return account.get();
endfunction

"""


def main():
    # create our private / public key pair
    entity = Entity()
    address = Address(entity)

    # create another address
    other = Entity()
    other_address = Address(other)

    # build the ledger API
    api = LedgerApi('127.0.0.1', 8000)

    # ensure that we have some funds for the time being
    api.sync(api.tokens.wealth(entity, 10000))

    print('Entity1:', api.tokens.balance(address))
    print('Entity2:', api.tokens.balance(other_address))

    # create the smart contract
    contract = SmartContract(CONTRACT_TEXT)

    # deploy the contract to the network
    api.sync(api.contracts.create(entity, contract, 2000))

    # interact with the contract
    balance1 = contract.query(api, 'balance', address=address)
    balance2 = contract.query(api, 'balance', address=other_address)
    print('Balance1: {}'.format(balance1))
    print('Balance2: {}'.format(balance2))

    print('Entity1:', api.tokens.balance(entity))
    print('Entity2:', api.tokens.balance(other))

    # transfer from one to the other using our newly deployed contract
    api.sync(contract.action(api, 'transfer', 40, [entity], address, other_address, 200))

    # interact with the contract
    balance1 = contract.query(api, 'balance', address=address)
    balance2 = contract.query(api, 'balance', address=other_address)
    print('Balance1: {}'.format(balance1))
    print('Balance2: {}'.format(balance2))

    print('Entity1:', api.tokens.balance(entity))
    print('Entity2:', api.tokens.balance(other))


if __name__ == '__main__':
    main()
