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
from fetchai.ledger.api.token import TokenTxFactory
from fetchai.ledger.crypto import Entity
from fetchai.ledger.crypto.deed import Deed, Operation
from fetchai.ledger.transaction import Transaction

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

    # we generate an identity from a known key, which contains funds.
    multi_sig_identity = Entity.from_hex("6e8339a0c6d51fc58b4365bf2ce18ff2698d2b8c40bb13fcef7e1ba05df18e4b")

    # generate a board to control multi-sig account, with variable voting weights
    board = [
        Entity.from_hex("e833c747ee0aeae29e6823e7c825d3001638bc30ffe50363f8adf2693c3286f8"),
        Entity.from_hex("4083a476c4872f25cb40839ac8d994924bcef12d83e2ba4bd3ed6c9705959860"),
        Entity.from_hex("20293422c4b5faefba3422ed436427f2d37f310673681e98ac8637b04e756de3"),
        Entity.from_hex("d5f10ad865fff147ae7fcfdc98b755452a27a345975c8b9b3433ff16f23495fb"),
    ]

    voting_weights = {
        board[0]: 1,
        board[1]: 1,
        board[2]: 1,
        board[3]: 2,
    }

    # generate another entity as a target for transfers
    other_identity = Entity.from_hex("7da0e3fa62a916238decd4f54d43301c809595d66dd469f82f29e076752b155c")

    # submit deed
    print("\nCreating deed...")
    deed = Deed()
    for sig, weight in voting_weights.items():
        deed.set_signee(sig, weight)
    deed.set_operation(Operation.amend, 4)
    deed.set_operation(Operation.transfer, 3)

    api.sync(api.tokens.deed(multi_sig_identity, deed, 500))

    # display balance before
    print("\nBefore remote-multisig transfer")
    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))
    print()

    # scatter/gather example
    print("Generating transaction and distributing to signers...")

    # add intended signers to transaction
    ref_tx = TokenTxFactory.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board)
    api.set_validity_period(ref_tx)

    # make a reference payload that can be used in this script for validation
    reference_payload = ref_tx.encode_payload()

    # have signers individually sign transaction
    signed_txs = []
    for signer in board:
        # signer builds their own transaction to compare to note that each of the signers will need to agree on all
        # parts of the message including the validity period and the counter
        signer_tx = TokenTxFactory.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board)
        signer_tx.counter = ref_tx.counter
        signer_tx.valid_until = ref_tx.valid_until
        signer_tx.valid_from = ref_tx.valid_from

        # sanity check each of the signers payload should match the reference payload
        assert signer_tx.encode_payload() == reference_payload

        # signers locally sign there version of the transaction
        signer_tx.sign(signer)

        # simulate distribution of signed partial transactions
        signed_txs.append(signer_tx.encode_partial())

    # gather and encode final transaction - this step in theory can be done by all the signers provided they are
    # received all the signature shares
    print("Gathering and combining signed transactions...")
    partial_txs = [Transaction.decode_partial(s)[1] for s in signed_txs]

    # merge them together into one fully signed transaction
    success, tx = Transaction.merge(partial_txs)
    assert success  # this indicates that all the signatures have been merged and that the transaction now validates

    # submit the transaction
    api.sync(api.submit_signed_tx(tx))

    print("\nAfter remote multisig-transfer")
    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))

    # round-robin example
    print("\nGenerating transaction and sending down the line of signers...")

    # create the basis for the transaction
    tx = TokenTxFactory.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board)
    api.set_validity_period(tx)

    # serialize and send to be signed
    tx_payload = tx.encode_payload()

    # have signers individually sign transaction and pass on to next signer
    for signer in board:
        # build the target transaction
        signer_tx = Transaction.decode_payload(tx_payload)

        # Signer decodes payload to inspect transaction
        signer_tx.sign(signer)

        # ensure that when we merge the signers signature into the payload that it is correct
        assert tx.merge_signatures(signer_tx)

    # once all the partial signatures have been merged then it makes sense
    print("Collecting final signed transaction...")
    assert tx.is_valid()
    api.sync(api.submit_signed_tx(tx))

    print("\nAfter remote multisig-transfer")
    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))


if __name__ == '__main__':
    main()
