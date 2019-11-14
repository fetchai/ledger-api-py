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


def main():
    # create the APIs
    api = LedgerApi(HOST, PORT)

    # generate a random identity
    multi_sig_identity = Entity()
    # generate a board to control multi-sig account, with variable voting weights
    board = {
        Entity(): 1,
        Entity(): 1,
        Entity(): 2,
    }
    # generate another entity as a target for transfers
    other_identity = Entity()

    print('Balance Before:', api.tokens.balance(multi_sig_identity))

    # create the balance
    print('Submitting wealth creation...')
    api.sync(api.tokens.wealth(multi_sig_identity, 100000000))
    print('Balance after wealth:', api.tokens.balance(multi_sig_identity))

    # Transfers can happen normally without a deed
    print('Submitting transfer...')
    api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20))

    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))

    # Submit deed
    deed = Deed(multi_sig_identity)
    for sig, weight in board.items():
        deed.add_signee(sig, weight)
    deed.amend_threshold = 4
    deed.transfer_threshold = 2

    api.sync(api.tokens.deed(multi_sig_identity, deed))

    # Original address can no longer validate transfers
    # api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20))

    # Sufficient voting power required to sign transfers
    api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20, signatories=board))

    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))

    b1 = list(board.keys())[2]
    #
    # tx = api.tokens._create_skeleton_tx(1000)
    # tx.from_address = Address(multi_sig_identity)
    # tx.add_transfer(Address(other_identity), 250)
    # tx.add_signer(b1)
    #
    # te = encode_transaction(tx, [b1])
    #
    # api.sync(api.tokens._post_tx_json(te, 'transfer'))

    api.sync(api.tokens.transfer(multi_sig_identity, other_identity, 250, 20, signatories={b1: 1}))

    print('Balance 1:', api.tokens.balance(multi_sig_identity))
    print('Balance 2:', api.tokens.balance(other_identity))


if __name__ == '__main__':
    main()
