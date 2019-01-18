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

import ecdsa
import binascii
import base64


def print_indiviadual_key(key, prefix=""):
    print("{}key [hex PEM,  hex]: {}".format(prefix, binascii.hexlify(key.to_pem())))
    print("{}key [hex DER,  hex]: {}".format(prefix, binascii.hexlify(key.to_der())))
    print("{}key [to_string,hex]: {}".format(prefix, binascii.hexlify(key.to_string())))
    print("{}key [to_string,b64]: {}".format(prefix, base64.b64encode(key.to_string())))
    print("{}key len [to_string,hex]: {}".format(prefix, len(binascii.hexlify(key.to_string()))))


def printKey(privateKey):
    print_indiviadual_key(privateKey, "private ")
    print_indiviadual_key(privateKey.get_verifying_key(), "public  ")


def main():
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    printKey(sk)

    data_tyo_sign = b"message"
    signature = sk.sign(data_tyo_sign)
    assert sk.get_verifying_key().verify(signature, data_tyo_sign)


if __name__ == '__main__':
    main()
