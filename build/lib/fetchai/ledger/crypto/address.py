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

import binascii
import hashlib

import base58

from .identity import Identity


class Address:
    BYTE_LENGTH = 32
    CHECKSUM_SIZE = 4
    DISPLAY_BYTE_LENGTH = BYTE_LENGTH + CHECKSUM_SIZE

    def __init__(self, identity):
        if isinstance(identity, Address):
            self._address = identity._address
            self._display = identity._display

        elif isinstance(identity, Identity):
            self._address = self._digest(identity.public_key_bytes)
            self._display = self._calculate_display(self._address)

        elif isinstance(identity, bytes):
            if len(identity) != self.BYTE_LENGTH:
                raise RuntimeError('Incorrect length of binary address')

            self._address = identity
            self._display = self._calculate_display(self._address)

        elif isinstance(identity, str):
            identity_bytes = base58.b58decode(identity)

            if len(identity_bytes) != self.DISPLAY_BYTE_LENGTH:
                raise RuntimeError('Unable to parse address, incorrect size')

            # split the identity into address and checksum
            address_raw = identity_bytes[:self.BYTE_LENGTH]
            checksum = identity_bytes[self.BYTE_LENGTH:]

            # calculate the expected checksum
            expected_checksum = self._calculate_checksum(address_raw)

            if checksum != expected_checksum:
                raise RuntimeError('Invalid checksum')

            # update internals
            self._address = address_raw
            self._display = identity

        else:
            raise RuntimeError('Failed to build identity from input')

    def __str__(self):
        return self._display

    def __bytes__(self):
        return self._address

    def __hash__(self):
        return hash(self._address)

    def __eq__(self, other):
        return bytes(self) == bytes(other)

    def to_hex(self):
        return binascii.hexlify(self._address).decode()

    @classmethod
    def _digest(cls, data):
        hash_func = hashlib.sha256()
        hash_func.update(data)
        return hash_func.digest()

    @classmethod
    def _calculate_checksum(cls, address_raw):
        return cls._digest(address_raw)[:cls.CHECKSUM_SIZE]

    @classmethod
    def _calculate_display(cls, address_raw):
        return base58.b58encode(address_raw + cls._digest(address_raw)[:cls.CHECKSUM_SIZE]).decode()
