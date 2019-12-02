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

# Demonstrates the distributed sharing of a multi-sig transaction before submisssion
import io

from build.lib.fetchai.ledger.crypto import Address
from fetchai.ledger.api import LedgerApi
from fetchai.ledger.transaction import TransactionFactory, Transaction
from fetchai.ledger.crypto import Entity
from fetchai.ledger.crypto.deed import Deed
from fetchai.ledger.serialisation import transaction, bytearray
from fetchai.ledger.serialisation.transaction import decode_transaction, encode_multisig_transaction

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
    print('\nSubmitting wealth creation...')
    api.sync(api.tokens.wealth(multi_sig_identity, 100000))
    print('Balance after wealth:', api.tokens.balance(multi_sig_identity))

    # Submit deed
    print("\nCreating deed...")
    deed = Deed(multi_sig_identity)
    for sig, weight in voting_weights.items():
        deed.add_signee(sig, weight)
    deed.amend_threshold = 4
    deed.transfer_threshold = 3

    api.sync(api.tokens.deed(multi_sig_identity, deed))

    # Display balance before
    print("\nBefore remote-multisig transfer")
    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))
    print()

    # Sufficient voting power required to sign transfers
    print("\nSubmitting transfer with two signatures with total 3 votes...")
    print_signing_votes(voting_weights, board[:3])

    # Add intended signers to transaction
    tx = TransactionFactory.transfer(api.tokens, multi_sig_identity, other_identity, 250, 20, signatories=board)

    # Serialize and send to be signed
    stx = tx.payload

    # Have signers individually sign transaction
    signed_txs = []
    for signer in board:
        # Signer decodes payload to inspect transaction
        itx = Transaction.from_payload(stx)
        print("Signer {} signing transaction:".format(signer.public_key[:8]))
        for k, v in itx.transfers.items():
            print("\tPay {} FET from {} to {}".format(v, str(itx.from_address)[:8], str(k)[:8]))

        # Signers locally decode transaction
        signature = signer.sign(stx)

        # Signer returns signed payload to originator
        signed_txs.append(signature)

    # Gather and encode final transaction
    # TODO: signatures must be in order!
    # signed_txs.reverse()
    encoded_tx = encode_multisig_transaction(tx, signed_txs)

    api.sync(api.tokens._post_tx_json(encoded_tx, 'transfer'))

    print("\nAfter remote multisig-transfer")
    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))


if __name__ == '__main__':
    main()