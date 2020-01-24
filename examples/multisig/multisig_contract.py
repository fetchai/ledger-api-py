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
function transfer(from: Address, to: Address, value: UInt64) : Int64

    if(!from.signedTx())
      return 0i64;
    endif

    use balance_state[from, to];
    var from_balance = balance_state.get(from, 0u64);
    var to_balance = balance_state.get(to, 0u64);

    if(from_balance < value)
      return 0i64;
    endif

    var u_from = from_balance - value;
    var u_to = to_balance + value;

    balance_state.set(from, u_from);
    balance_state.set(to, u_to);
    return 1i64;

endfunction

"""


def print_address_balances(api: LedgerApi, contract: Contract, addresses: List[Address]):
    for idx, address in enumerate(addresses):
        print('Address{}: {:<6d} bFET {:<10d} TOK'.format(idx, api.tokens.balance(address),
                                                          contract.query(api, 'balanceOf', address=address)))
    print()


def main():
    # generate a random identity
    multi_sig_identity = Entity.from_hex("e833c747ee0aeae29e6823e7c825d3001638bc30ffe50363f8adf2693c3286f8")

    # create our first private key pair
    multi_sig_address = Address(multi_sig_identity)

    # generate a board to control multi-sig account, with variable voting weights
    board = []
    board.append(Entity.from_hex("6e8339a0c6d51fc58b4365bf2ce18ff2698d2b8c40bb13fcef7e1ba05df18e4b"))
    board.append(Entity.from_hex("4083a476c4872f25cb40839ac8d994924bcef12d83e2ba4bd3ed6c9705959860"))
    board.append(Entity.from_hex("7da0e3fa62a916238decd4f54d43301c809595d66dd469f82f29e076752b155c"))
    board.append(Entity.from_hex("20293422c4b5faefba3422ed436427f2d37f310673681e98ac8637b04e756de3"))

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

    # # create wealth so that we have the funds to be able to create contracts on the network
    # api.sync(api.tokens.wealth(multi_sig_identity, 10000))
    # api.sync([api.tokens.wealth(sig, 10000) for sig in board])

    # create a multisig deed for multi_sig_identity
    print("\nCreating deed...")
    deed = Deed()
    for sig, weight in voting_weights.items():
        deed.set_signee(sig, weight)
    deed.amend_threshold = 4
    # Both the transfer and execute thresholds must be met to create a contract
    # TODO: Contract creation both requires meeting the thresholds below, and can only be signed by a single
    #  signatory. Therefore a single board member must be able to exceed these thresholds for creation
    deed.set_threshold(Operation.execute, 2)
    deed.set_threshold(Operation.transfer, 2)

    # Submit deed
    # api.sync(api.tokens.deed(multi_sig_identity, deed))

    # create the smart contract
    print('\nSetting up smart contract')
    contract = Contract(CONTRACT_TEXT, multi_sig_identity, bytes.fromhex('590953aea8a09c51'))

    # TODO: Must be signed by single board member with sufficient votes
    tx = contract.create(contract_factory, multi_sig_identity, 4000, [board[3]])
    tx.sign(board[3])

    api.sync(api.contracts.submit_signed_tx(tx, tx.signers))

    # print the current status of all the tokens
    print('-- BEFORE --')
    print_address_balances(api, contract, [multi_sig_address, address2])

    # transfer from one to the other using our newly deployed contract
    tok_transfer_amount = 200
    fet_tx_fee = 160

    print("Building contract call transaction...")
    tx = contract.action(contract_factory, 'transfer', fet_tx_fee, multi_sig_address, address2, tok_transfer_amount,
                         signers=board)
    for signer in board:
        tx.sign(signer)

    api.sync(api.contracts.submit_signed_tx(tx, tx.signers))

    print('-- AFTER --')
    print_address_balances(api, contract, [multi_sig_address, address2])


if __name__ == '__main__':
    main()
