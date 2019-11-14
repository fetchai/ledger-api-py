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
# How to send transactions over HTTP using the Python SDK
#
from build.lib.fetchai.ledger.serialisation import encode_transaction
from fetchai.ledger.api import LedgerApi
from fetchai.ledger.crypto import Identity, Entity, Address
from fetchai.ledger.crypto.deed import Deed
from fetchai.ledger.transaction import Transaction

HOST = '127.0.0.1'
PORT = 8000


def print_signing_votes(voting_weights, signers):
    if not isinstance(signers, list):
        signers = [signers]
    votes = [voting_weights[s] for s in signers]
    print("Votes: {} Total weight: {}".format(', '.format(str(v) for v in votes), sum(votes)))


def main():
    # create the APIs
    api = LedgerApi(HOST, PORT)

    # generate a random identity
    multi_sig_identity = Entity()
    # generate a board to control multi-sig account, with variable voting weights
    board = [Entity() for _ in range(4)]
    voting_weights = {
        board[0]: 1,
        board[1]: 1,
        board[2]: 1,
        board[3]: 2,
    }
    # generate another entity as a target for transfers
    other_identity = Entity()

    # Create the balance
    print('Submitting wealth creation...')
    api.sync(api.tokens.wealth(multi_sig_identity, 100000000))
    print('Balance after wealth:', api.tokens.balance(multi_sig_identity))

    # Transfers can happen normally without a deed
    print('Submitting pre-deed transfer with original signature...')
    api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20))

    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))

    # Submit deed
    print("Creating deed...")
    deed = Deed(multi_sig_identity)
    for sig, weight in voting_weights.items():
        deed.add_signee(sig, weight)
    deed.amend_threshold = 4
    deed.transfer_threshold = 2

    api.sync(api.tokens.deed(multi_sig_identity, deed))

    # Original address can no longer validate transfers
    print("Transfer with original signature should fail...")
    try:
        api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20))
    except RuntimeError as e:
        print("Transaction failed as expected")
    else:
        print("Transaction succeeded, it shouldn't have")

    # Sufficient voting power required to sign transfers
    print("Submitting transfer with two signatures with total 2 votes...")
    print_signing_votes(voting_weights, board[:2])
    api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board[:2]))

    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))

    # Some entities may have more voting power
    print("Submitting transfer with single signature with 2 votes")
    print_signing_votes(voting_weights, board[3])
    api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20, signatories=[board[3]]))
    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))

    # Amend the deed
    print("Amending deed to increase transfer threshold to 3 votes")
    deed.transfer_threshold = 3
    api.sync(api.tokens.deed(multi_sig_identity, deed, board))

    # Single member no longer has enough voting power
    print("Single member transfer with 2 votes should no longer succeed...")
    try:
        print_signing_votes(voting_weights, board[3])
        api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20, signatories=[board[3]]))
    except RuntimeError as e:
        print("Transaction failed as expected")
    else:
        print("Transaction succeeded, it shouldn't have")

    # Correct number of signatory votes
    print("Succesful transaction with sufficient voting weight...")
    print_signing_votes(voting_weights, board[1:])
    api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board[1:]))

    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))


if __name__ == '__main__':
    main()
