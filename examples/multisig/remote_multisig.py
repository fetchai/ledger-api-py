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

# Demonstrates the distributed sharing of a multi-sig transaction before submission

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.transaction import Transaction
from fetchai.ledger.api.token import TokenTxFactory
from fetchai.ledger.crypto import Entity
from fetchai.ledger.crypto.deed import Deed, Operation

HOST = '127.0.0.1'
PORT = 8000


def print_signing_votes(voting_weights, signers):
    if not isinstance(signers, list):
        signers = [signers]
    votes = [voting_weights[s] for s in signers]
    print("Votes: {} Total weight: {}".format(', '.join(str(v) for v in votes), sum(votes)))


def main():
    # create the APIs
    api = LedgerApi(HOST, PORT)

    # generate a random identity
    multi_sig_identity = Entity.from_hex("6e8339a0c6d51fc58b4365bf2ce18ff2698d2b8c40bb13fcef7e1ba05df18e4b")
    # generate a board to control multi-sig account, with variable voting weights
    #board = [Entity() for _ in range(4)]

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
    other_identity = Entity.from_hex("7da0e3fa62a916238decd4f54d43301c809595d66dd469f82f29e076752b155c")

    # Submit deed
    print("\nCreating deed...")
    deed = Deed()
    for sig, weight in voting_weights.items():
        deed.set_signee(sig, weight)
    deed.amend_threshold = 4
    deed.set_threshold(Operation.transfer, 3)

    api.sync(api.tokens.deed(multi_sig_identity, deed))

    # Display balance before
    print("\nBefore remote-multisig transfer")
    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))
    print()

    ## Scatter/gather example
    print("Generating transaction and distributing to signers...")

    # Add intended signers to transaction
    tx = TokenTxFactory.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board)
    api.tokens._set_validity_period(tx)

    # Serialize and send to be signed
    stx = tx.encode_partial()

    # Have signers individually sign transaction
    signed_txs = []
    for signer in board:
        # Signer builds their own transaction to compare to
        signer_tx = TokenTxFactory.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board)

        # Signer decodes payload to inspect transaction
        itx = Transaction.decode_partial(stx)

        # Some transaction details aren't expected to match/can't be predicted
        signer_tx.valid_until = itx.valid_until
        print("itx.counter before ")
        print(itx.counter)
        print("itx.counter after ")
        signer_tx.counter = itx.counter

        print("Transactions match" if signer_tx.compare(itx) else
              "Transactions do not match")

        # Signers locally decode transaction
        itx.sign(signer)

        # Serialize for return to origin
        signed_txs.append(itx.encode_partial())

    # Gather and encode final transaction
    print("Gathering and combining signed transactions...")
    stxs = [Transaction.decode_partial(s) for s in signed_txs]
    for st in stxs:
        tx.merge_signatures(st)
    api.sync(api.tokens.submit_signed_tx(tx, tx.signers))

    print("\nAfter remote multisig-transfer")
    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))

    # Round robin example
    print("\nGenerating transaction and sending down the line of signers...")
    # Add intended signers to transaction
    tx = TokenTxFactory.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board)
    api.tokens._set_validity_period(tx)

    # Serialize and send to be signed
    stx = tx.encode_partial()

    # Have signers individually sign transaction and pass on to next signer
    for signer in board:
        # Signer builds their own transaction to compare to
        signer_tx = TokenTxFactory.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board)

        # Signer decodes payload to inspect transaction
        itx = Transaction.decode_partial(stx)

        # Some transaction details aren't expected to match/can't be predicted
        signer_tx.valid_until = itx.valid_until
        signer_tx.counter = itx.counter

        print("Transactions match" if signer_tx.compare(itx) else
              "Transactions do not match")

        # Signers locally decode transaction
        itx.sign(signer)

        # Signer re-encodes transaction and forwards to the next signer
        stx = itx.encode_partial()

    # Gather and encode final transaction
    print("Collecting final signed transaction...")
    itx = Transaction.decode_partial(stx)
    api.sync(api.tokens.submit_signed_tx(itx, itx.signers))

    print("\nAfter remote multisig-transfer")
    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))


if __name__ == '__main__':
    main()