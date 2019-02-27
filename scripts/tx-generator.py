#!/usr/bin/env python3
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

from fetchai.ledger.crypto import Signing
from fetchai.ledger.serialisation.objects import Tx
from fetchai.ledger.serialisation.objects.transaction_api import create_transfer_tx, create_wealth_tx

import base64
import binascii
import argparse


def create_signed_transfer_transaction(priv_keys_from, address_to_bin, amount, fee):
    address_from_bin = priv_keys_from[0].get_verifying_key().to_string()

    tx = create_transfer_tx(address_from_bin, address_to_bin, amount, fee)

    for pk in priv_keys_from:
        tx.sign(pk)

    return tx


def create_signed_wealth_transaction(priv_keys_to, amount, fee):
    address_to_bin = priv_keys_to[0].get_verifying_key().to_string()

    tx = create_wealth_tx(address_to_bin, amount, fee)

    for pk in priv_keys_to:
        tx.sign(pk)

    return tx


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Generates transfer Transaction in Wire Format.")
    subparsers = parser.add_subparsers(dest="subcommand")

    transfer_tx_parser = subparsers.add_parser('create-transfer-tx')
    transfer_tx_parser.add_argument('-p', '--private-key', type=str, nargs='+', help='Base64 or Hex encoded Private key (EDCSA secp256k1 in canonical binary form. Provide `hex:` prefix if value is hex encoded, base64 encoding is assumed if no prefix is provided. The FIRST private key will be used to derive the `FROM` identity (public key) to make transfer from. If omitted, single private key will be generated.)')
    transfer_tx_parser.add_argument('-t', '--public-key-to', type=str, help='Base64 or Hex encoded Public key(EDCSA secp256k1 in canonical binary form) representing `TO` (destination) identity. Provide `hex:` prefix if value is hex encoded, base64 encoding is assumed if no prefix is provided. If omitted, it will be generated.')
    transfer_tx_parser.add_argument('-a', '--amount', type=int, help='Amount to transfer. Must be unsigned integer (64 bites).', default=100)
    transfer_tx_parser.add_argument('-f', '--fee', type=int, help='Fee. Must be unsigned integer (64 bites).', default=1)
    transfer_tx_parser.add_argument('-m', '--include_metadata', action='store_true', help='Include non-mandatory metadata section.')

    wealth_tx_parser = subparsers.add_parser('create-wealth-tx')
    wealth_tx_parser.add_argument('-p', '--private-key', type=str, nargs='+', help='Base64 or Hex encoded Private key (EDCSA secp256k1 in canonical binary form. Provide `hex:` prefix if value is hex encoded, base64 encoding is assumed if no prefix is provided. The FIRST private key will be used to derive the `FROM` identity (public key) to make transfer from. If omitted, single private key will be generated.)')
    wealth_tx_parser.add_argument('-a', '--amount', type=int, help='Amount to transfer. Must be unsigned integer (64 bites).', default=100)
    wealth_tx_parser.add_argument('-f', '--fee', type=int, help='Fee. Must be unsigned integer (64 bites).', default=1)
    wealth_tx_parser.add_argument('-m', '--include_metadata', action='store_true', help='Include non-mandatory metadata section.')

    verify_tx_parser = subparsers.add_parser('verify-tx')
    v_group = verify_tx_parser.add_mutually_exclusive_group(required=True)
    v_group.add_argument('-t', '--tx-wire-format-string', type=str, help='Transaction in wire format, for example -t \'{"ver":"1.0", "data":"..."}\'.')
    v_group.add_argument('-f', '--filename', type=str, help='Filename containing transaction in wire format.')
    verify_tx_parser.add_argument('-m', '--print_metadata', action='store_true', help='Include non-mandatory metadata section.')

    return parser.parse_args(args)


def decode(hex_or_base64_encoded_val):
    split_res = hex_or_base64_encoded_val.split(':', 1)

    if len(split_res) == 2:
        key, value = split_res
    else:
        key = "b64"
        value = hex_or_base64_encoded_val

    if key == "b64":
        dec_val = base64.b64decode(value)
    elif key == 'hex':
        dec_val = binascii.unhexlify(value)
    else:
        raise ValueError("Unexpected encoding type '{}' provided as prefix.".format(key))

    return dec_val


def get_private_keys(b64_encoded_priv_keys):
    keys = []
    for pk in b64_encoded_priv_keys:
        dec_priv_key = decode(pk)
        keys.append(Signing.create_private_key(dec_priv_key))
    assert len(keys) == len(set(keys)), "Private keys in provided list are not unique (some of them are provided multiple times)."
    return keys


def main():
    args = parse_args()

    if args.subcommand == 'create-transfer-tx':
        if args.private_key:
            priv_keys = get_private_keys(args.private_key)
        else:
            priv_keys = [Signing.generate_private_key()]

        if args.public_key_to:
            pub_key_to_bin = decode(args.public_key_to)
        else:
            pub_key_to_bin = Signing.generate_private_key().get_verifying_key().to_string()

        tx = create_signed_transfer_transaction(priv_keys, pub_key_to_bin, amount=args.amount, fee=args.fee)
        print(tx.to_wire_format(include_metadata=args.include_metadata))

    elif args.subcommand == 'create-wealth-tx':
        if args.private_key:
            priv_keys = get_private_keys(args.private_key)
        else:
            priv_keys = [Signing.generate_private_key()]

        tx = create_signed_wealth_transaction(priv_keys, amount=args.amount, fee=args.fee)
        print(tx.to_wire_format(include_metadata=args.include_metadata))

    elif args.subcommand == 'verify-tx':
        if args.filename:
            with open(args.filename, 'r') as f:
                wire_tx = f.read()
        else:
            wire_tx = args.tx_wire_format_string

        tx = Tx.from_wire_format(wire_tx)

        if args.print_metadata:
            print(tx)
            #print("hex:\n{}".format(tx))
            #print("bin64:\n{}".format(tx.getMetadataDict()))

        if tx.verify():
            msg = "SUCCESSFULLY verified."
        else:
            msg = "FAILED to verify."
        print(msg)


if __name__ == '__main__':
    main()
