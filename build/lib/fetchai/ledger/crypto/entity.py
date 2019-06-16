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
import binascii

import ecdsa

from .identity import Identity


class Entity(Identity):
    """
    An entity is a full private/public key pair.
    """

    @staticmethod
    def from_hex(private_key_hex: str):
        return Entity(binascii.unhexlify(private_key_hex))

    @staticmethod
    def from_base64(private_key_base64: str):
        return Entity(base64.b64decode(private_key_base64))

    def __init__(self, private_key_bytes=None):

        # construct or generate the private key if one is not specified
        if private_key_bytes is None:
            self._signing_key = ecdsa.SigningKey.generate(curve=self.curve, hashfunc=self.hash_function)
        elif isinstance(private_key_bytes, bytes):
            self._signing_key = ecdsa.SigningKey.from_string(private_key_bytes, curve=self.curve,
                                                             hashfunc=self.hash_function)
        else:
            raise RuntimeError('Unable to load private key from input')

        # cache the binary representations of the private key
        self._private_key_bytes = self._signing_key.to_string()
        self._private_key = base64.b64encode(self._private_key_bytes).decode()

        # construct the base class
        super().__init__(self._signing_key.get_verifying_key())

    @property
    def private_key(self):
        return self._private_key

    @property
    def private_key_hex(self):
        return binascii.hexlify(self.private_key_bytes).decode()

    @property
    def private_key_bytes(self):
        return self._private_key_bytes

    @property
    def signing_key(self):
        return self._signing_key

    def sign(self, message: bytes):
        return self._signing_key.sign(message)
