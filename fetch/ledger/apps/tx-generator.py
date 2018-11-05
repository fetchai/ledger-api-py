#!/usr/bin/env python3
#------------------------------------------------------------------------------
#
#   Copyright 2018 Fetch.AI Limited
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
#------------------------------------------------------------------------------


from fetch.ledger.chain import Tx, Identity
from fetch.ledger.crypto import Signing

import json
import base64
import argparse
from io import BytesIO
from ecdsa import VerifyingKey
from sys import argv

def serialise_identity(identity):
    stream = BytesIO()
    identity.serialise(stream)
    return stream.getvalue()

def create_transfer_contract(identity_from, identity_to, amount):
    contract = { 
        "from": base64.b64encode(serialise_identity(identity_from)).decode(),
        "to": base64.b64encode(serialise_identity(identity_to)).decode(),
        "amount": amount
        }
    contract_json_str = json.dumps(contract)
    return contract_json_str.encode()

def create_transfer_transaction(priv_keys_from, pub_key_to, amount, fee):
    identity_from = Identity(data=priv_keys_from[0].get_verifying_key().to_string())

    if isinstance(pub_key_to, VerifyingKey):
        pub_key_to = pub_key_to.to_string()
    elif not isinstance(pub_key_to, bytes):
        raise TypeError("Unexpected type of `public_key_to` parameter, it must be either instance of `VerfyingKey` class or `bytes` type.")

    identity_to = Identity(data=pub_key_to)

    tx = Tx()
    tx.contract_name = b'fetch.token.transfer'
    tx.data = create_transfer_contract(identity_from, identity_to, amount)
    tx.fee = fee
    tx.resources = [serialise_identity(identity_from), serialise_identity(identity_to)]

    for pk in priv_keys_from:
        tx.sign(pk)

    return tx

def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Generates transfer Transaction in Wire Format.")
    parser.add_argument('-p', '--private-key', type=str, nargs='+', help='Base64 encoded Private key (EDCSA secp256k1 in canonical binary form. The FIRST private key will be used to derive the `FROM` identity (public key) to make transfer from. If omitted, single private key will be generated.)')
    parser.add_argument('-t', '--public-key-to', type=str, help='Base64 encoded Public key(EDCSA secp256k1 in canonical binary form) representing `TO` (destination) identity. If omitted, it will be generated.')
    parser.add_argument('-a', '--amount', type=int, help='Amount to transfer. Must be unsigned integer (64 bites).', default=100)
    parser.add_argument('-f', '--fee', type=int, help='Fee. Must be unsigned integer (64 bites).', default=1)
    parser.add_argument('-m', '--include_metadata', action='store_true', help='Include non-mandatory metadata section.')
    return parser.parse_args(args)

def get_private_keys(b64_encoded_priv_keys):
    keys = set()
    for pk in b64_encoded_priv_keys:
        keys.add(Signing.privKeyFromBin(base64.b64decode(pk)))
    return keys

def main():
    args = parse_args()

    if args.private_key:
        priv_keys = get_private_keys(args.private_key)
    else:
        priv_keys = [Signing.generatePrivKey()]

    if args.public_key_to:
        pub_key_to = Signing.pubKeyFromBin(base64.b64decode(args.public_key_to))
    else:
        pub_key_to = Signing.generatePrivKey().get_verifying_key()

    tx = create_transfer_transaction(priv_keys, pub_key_to, amount=args.amount, fee=args.fee)
    print(tx.toWireFormat(include_metadata=args.include_metadata))

if __name__ == '__main__':
    main()
