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
import hashlib


class Signing(object):
    curve = ecdsa.SECP256k1
    digest = hashlib.sha256

    @classmethod
    def generate_private_key(cls):
        return ecdsa.SigningKey.generate(curve=cls.curve)

    @classmethod
    def create_private_key(cls, private_key_data):
        return ecdsa.SigningKey.from_string(private_key_data, curve=cls.curve)

    @classmethod
    def create_public_key(cls, public_key_data):
        return ecdsa.VerifyingKey.from_string(public_key_data, curve=cls.curve)
