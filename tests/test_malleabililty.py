from fetchai.ledger.api import LedgerApi, submit_json_transaction
from fetchai.ledger.crypto import Identity, Entity
import binascii
import base64

HOST = '127.0.0.1'
PORT = 8000


def main():
    ENDPOINT='transfer'
    # create the APIs
    api = LedgerApi(HOST, PORT)

    # Hardcoded private keys
    id1PrivateKey = "d222867ac019aa7e5b5946ee23100b4437d54ec08db8e89f6e459d497b579a03"
    id2PrivateKey = "499f40c1bf13e7716e62431b17ab668fa2688b7c94a011a3aab595477bc68347"

    # Create identities from the private keys
    id1 = Entity.from_hex(id1PrivateKey)
    id2 = Entity.from_hex(id2PrivateKey)

    # Load 1000 tokens to id1
    api.sync(api.tokens.wealth(id1, 1000))

    # signed transaction that transfers 250 FET from id1 to id2. Signed with (r,s)
    orig_tx = 'a1440000c5ab20e3ab845cb4a1d2c3e4c3b08f5ff42a6ff2a71d7697ba8f32c415b77c7f8d850b3ef025b189a2d9bb4a515a84c3673db6d3ef25385d2c8d1e34b06e2de1c0fac08501140000000000000000040bafbc61a08524372f495d9dee08adbc39824e980506947091395cece16636ddc094b9d409d5b34ef0bbd9c99c5caf21fc373802472cf96a8a280f84e833f992402192a0a125d551b60800d441cb3483cd36573c22a73f22563d6dd7b27e677b98ba4e2f77596888839a3c6f2439c97949ea28923f168d360a6d155c2be79570af'
    # signed Malicious transaction of the previous transaction. Signed with (r,n-s)
    mal_tx = 'a1440000c5ab20e3ab845cb4a1d2c3e4c3b08f5ff42a6ff2a71d7697ba8f32c415b77c7f8d850b3ef025b189a2d9bb4a515a84c3673db6d3ef25385d2c8d1e34b06e2de1c0fac08501140000000000000000040bafbc61a08524372f495d9dee08adbc39824e980506947091395cece16636ddc094b9d409d5b34ef0bbd9c99c5caf21fc373802472cf96a8a280f84e833f99240f1a0311cc9b42edaa41d537e3d1f9d54ac159504276c27be2973cea85c8e8a17148a2b1dc3e188f911c6b05f163d95b964ae594a347870973e59b3c93d35b895'

    # Creating jsons for the above mentioned transactions
    legit_trans = submit_json_transaction(host="localhost", port=8000, tx_data=dict(ver="1.2", data=base64.b64encode(binascii.unhexlify(orig_tx)).decode()), endpoint='fetch/token/transfer')
    mal_trans = submit_json_transaction(host="localhost", port=8000, tx_data=dict(ver="1.2", data=base64.b64encode(binascii.unhexlify(mal_tx)).decode()), endpoint='fetch/token/transfer')
    # legit_trans = api.tokens._post_tx_json(binascii.unhexlify(orig_tx), ENDPOINT)
    # mal_trans = api.tokens._post_tx_json(binascii.unhexlify(mal_tx), ENDPOINT)
    # Sending the transactions to the ledger

    assert legit_trans == mal_trans, "Malleable transactions have different transaction hash"
    api.sync([legit_trans, mal_trans])

    # If transaction malleability is feasible, id2 should have 500 FET.
    # If balance of id2 is more than 250 raise an assert
    assert api.tokens.balance(id2) == 250, "Vulnerable to transaction malleability attack"


if __name__ == '__main__':
    main()