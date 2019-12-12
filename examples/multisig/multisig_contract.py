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
from fetchai.ledger.api.contracts import ContractTxFactory
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity, Address
from fetchai.ledger.crypto.deed import Deed, Operation

CONTRACT_TEXT = """
persistent sharded balance_state : UInt64;
persistent supply_state : UInt64;

@init
function init(owner: Address)

    use supply_state;
    use balance_state[owner];

    supply_state.set(92817u64);
    balance_state.set(owner, 92817u64);

endfunction

@query
function totalSupply(): UInt64

    use supply_state;
    return supply_state.get();

endfunction


@query
function balanceOf(address: Address) : UInt64

    use balance_state[address];
    return balance_state.get(address, 0u64);

endfunction

@action
function transfer(from: Address, to: Address, value: UInt64) : Bool

    if(!from.signedTx())
      return false;
    endif

    use balance_state[from, to];
    var from_balance = balance_state.get(from, 0u64);
    var to_balance = balance_state.get(to, 0u64);

    if(from_balance < value)
      return false;
    endif

    var u_from = from_balance - value;
    var u_to = to_balance + value;

    balance_state.set(from, u_from);
    balance_state.set(to, u_to);
    return true;

endfunction

"""


def print_address_balances(api: LedgerApi, contract: Contract, addresses: List[Address]):
    for idx, address in enumerate(addresses):
        print('Address{}: {:<6d} bFET {:<10d} TOK'.format(idx, api.tokens.balance(address),
                                                          contract.query(api, 'balanceOf', address=address)))
    print()


def main():
    # generate a random identity
    multi_sig_identity = Entity()

    # create our first private key pair
    multi_sig_address = Address(multi_sig_identity)

    # generate a board to control multi-sig account, with variable voting weights
    board = [Entity() for _ in range(4)]
    voting_weights = {
        board[0]: 1,
        board[1]: 1,
        board[2]: 1,
        board[3]: 2,
    }

    # create a second private key pair
    entity2 = Entity()
    address2 = Address(entity2)

    # build the ledger API
    api = LedgerApi('127.0.0.1', 8000)

    # create contract factory
    contract_factory = ContractTxFactory(api)

    # create wealth so that we have the funds to be able to create contracts on the network
    api.sync(api.tokens.wealth(multi_sig_identity, 10000))

    # create a multisig deed for multi_sig_identity
    # Submit deed
    print("\nCreating deed...")
    deed = Deed(multi_sig_identity)
    for sig, weight in voting_weights.items():
        deed.set_signee(sig, weight)
    deed.amend_threshold = 4
    # TODO: What is the correct operation for contract creation?
    deed.set_threshold(Operation.execute, 2)
    deed.set_threshold(Operation.create, 2)

    api.sync(api.tokens.deed(multi_sig_identity, deed))

    # create the smart contract
    contract = Contract(CONTRACT_TEXT, multi_sig_identity)

    tx = contract.create(contract_factory, multi_sig_identity, 4000, board)
    for signee in board:
        tx.sign(signee)

    # TODO: Will fail due to permission denied
    api.sync(api.contracts.submit_signed_tx(tx, tx.signers))

    # TODO: Complete the rest once contract creation succeeds
    # # print the current status of all the tokens
    # print('-- BEFORE --')
    # print_address_balances(api, contract, [multi_sig_address, address2])
    #
    # # transfer from one to the other using our newly deployed contract
    # tok_transfer_amount = 200
    # fet_tx_fee = 160
    # api.sync(contract.action(api, 'transfer', fet_tx_fee, [multi_sig_identity], multi_sig_address, address2, tok_transfer_amount))
    #
    # print('-- AFTER --')
    # print_address_balances(api, contract, [multi_sig_address, address2])


if __name__ == '__main__':
    main()
