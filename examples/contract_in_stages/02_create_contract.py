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
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity

CONTRACT_TEXT = """
persistent sharded balance : UInt64;

@init
function setup(owner : Address)
  use balance[owner];
  balance.set(owner, 1000000u64);
endfunction

@action
function transfer(from: Address, to: Address, amount: UInt64)

  use balance[from, to];
  
  // Check if the sender has enough balance to proceed
  if (balance.get(from) >= amount)

    // update the account balances
    balance.set(from, balance.get(from) - amount);
    balance.set(to, balance.get(to, 0u64) + amount);
  endif

endfunction

@query
function balance(address: Address) : UInt64
    use balance[address];
    return balance.get(address, 0u64);
endfunction

"""


def main():
    print('Loading private key...')

    # load up the previously created private key
    with open('private.key', 'r') as private_key_file:
        entity1 = Entity.prompt_load(private_key_file)

    print('Loading private key...complete')

    # build the ledger API
    api = LedgerApi('127.0.0.1', 8000)

    # create the smart contract
    contract = Contract(CONTRACT_TEXT, entity1)

    print('Deploying contract...')

    # deploy the contract to the network
    api.sync(api.contracts.create(entity1, contract, 2000))

    print('Deploying contract...complete')

    # save the contract to the disk
    with open('sample.contract', 'w') as contract_file:
        contract.dump(contract_file)


if __name__ == '__main__':
    main()
