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

#
# How to set the deed for a multi-sig account
#
from fetchai.ledger.api import LedgerApi
from fetchai.ledger.crypto import Entity
from fetchai.ledger.crypto.deed import Deed, Operation

HOST = '127.0.0.1'
PORT = 8000


def print_signing_votes(voting_weights, signers):
    if not isinstance(signers, list):
        signers = [signers]
    votes = [voting_weights[s] for s in signers]
    print("Votes: {} = {}".format(' + '.join(str(v) for v in votes), sum(votes)))


def main():
    # create the APIs
    api = LedgerApi(HOST, PORT)

    # generate a random identity
    multi_sig_identity = Entity.from_hex("6e8339a0c6d51fc58b4365bf2ce18ff2698d2b8c40bb13fcef7e1ba05df18e4b")
    # Generate a board to control multi-sig account, with variable voting weights.
    # We use keys for accounts which already have funds.
    board = []
    board.append(Entity.from_hex("e833c747ee0aeae29e6823e7c825d3001638bc30ffe50363f8adf2693c3286f8"))
    board.append(Entity.from_hex("4083a476c4872f25cb40839ac8d994924bcef12d83e2ba4bd3ed6c9705959860"))
    board.append(Entity.from_hex("20293422c4b5faefba3422ed436427f2d37f310673681e98ac8637b04e756de3"))
    board.append(Entity.from_hex("d5f10ad865fff147ae7fcfdc98b755452a27a345975c8b9b3433ff16f23495fb"))
    voting_weights = {
        board[0]: 1,
        board[1]: 1,
        board[2]: 1,
        board[3]: 2,
    }
    # generate another entity as a target for transfers
    other_identity = Entity.from_hex("e833c747ee0aeae29e6823e7c825d3001638bc30ffe50363f8adf2693c3286f8")

    print('Balance after wealth:', api.tokens.balance(multi_sig_identity))

    # Transfers can happen normally without a deed
    print('\nSubmitting pre-deed transfer with original signature...')
    api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20))

    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))

    # Submit deed
    print("\nCreating deed...")
    deed = Deed()
    for sig, weight in voting_weights.items():
        deed.set_signee(sig, weight)
    deed.amend_threshold = 4
    deed.set_threshold(Operation.transfer, 2)

    api.sync(api.tokens.deed(multi_sig_identity, deed))

    # Original address can no longer validate transfers
    print("\nTransfer with original signature should fail...")
    try:
        api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20))
    except RuntimeError as e:
        print("Transaction failed as expected")
    else:
        print("Transaction succeeded, it shouldn't have")

    # Sufficient voting power required to sign transfers
    print("\nSubmitting transfer with two signatures with total 2 votes...")
    print_signing_votes(voting_weights, board[:2])
    api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board[:2]))

    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))

    # Some entities may have more voting power
    print("\nSubmitting transfer with single signature with 2 votes...")
    print_signing_votes(voting_weights, board[3])
    api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20, signatories=[board[3]]))
    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))

    # Amend the deed
    print("\nAmending deed to increase transfer threshold to 3 votes...")
    deed.set_threshold(Operation.transfer, 3)
    api.sync(api.tokens.deed(multi_sig_identity, deed, board))

    # Single member no longer has enough voting power
    print("\nSingle member transfer with 2 votes should no longer succeed...")
    try:
        print_signing_votes(voting_weights, board[3])
        api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20, signatories=[board[3]]))
    except RuntimeError as e:
        print("Transaction failed as expected")
    else:
        print("Transaction succeeded, it shouldn't have")

    # Correct number of signatory votes
    print("\nSuccesful transaction with sufficient voting weight...")
    print_signing_votes(voting_weights, board[1:])
    api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board[1:]))

    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))

    # Warning: if no amend threshold is set, future amendments are impossible
    print("\nAmending deed to remove threshold...")
    deed.amend_threshold = None
    allow_no_amend = True
    api.sync(api.tokens.deed(multi_sig_identity, deed, board, allow_no_amend))

    deed.amend_threshold = 1
    print("\nExpecting further amendment to fail...")
    try:
        api.sync(api.tokens.deed(multi_sig_identity, deed, board))
    except RuntimeError as e:
        print("Transaction failed as expected")
    else:
        print("Transaction succeeded, it shouldn't have")


if __name__ == '__main__':
    main()
