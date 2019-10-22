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

import base64
import hashlib

import ecdsa


class Identity:
    """
    An identity is the public half of a private / public key pair
    """

    # these are hardcoded at the moment, but in more schemes will be supported in the future
    curve = ecdsa.SECP256k1
    hash_function = hashlib.sha256

    @staticmethod
    def from_hex(private_key_hex: str):
        return Identity(bytes.fromhex(private_key_hex))

    @staticmethod
    def from_base64(private_key_base64: str):
        return Identity(base64.b64decode(private_key_base64))

    def __init__(self, public_key):

        if isinstance(public_key, Identity):
            self._verifying_key = public_key.verifying_key
        elif isinstance(public_key, ecdsa.VerifyingKey):
            self._verifying_key = public_key
        elif isinstance(public_key, bytes):
            self._verifying_key = ecdsa.VerifyingKey.from_string(public_key, curve=self.curve,
                                                                 hashfunc=self.hash_function)
        else:
            raise RuntimeError('Failed')

        # cache the binary representations of the public key
        self._public_key_bytes = self._verifying_key.to_string()
        self._public_key = base64.b64encode(self._public_key_bytes).decode()

    def __eq__(self, other):
        return self.public_key_bytes == other.public_key_bytes

    def __ne__(self, other):
        return self.public_key_bytes != other.public_key_bytes

    def __hash__(self):
        return hash(self._public_key_bytes)

    @property
    def public_key(self):
        return self._public_key

    @property
    def public_key_hex(self):
        return self.public_key_bytes.hex()

    @property
    def public_key_bytes(self):
        return self._public_key_bytes

    @property
    def verifying_key(self):
        return self._verifying_key

    def verify(self, message: bytes, signature: bytes):
        success = False

        try:
            success = self._verifying_key.verify(signature, message)

        except ecdsa.keys.BadSignatureError:
            pass

        return success
