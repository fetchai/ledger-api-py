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

import base58

from fetchai.ledger.serialisation import sha256_hash
from .identity import Identity


class Address:
    BYTE_LENGTH = 32
    CHECKSUM_SIZE = 4
    DISPLAY_BYTE_LENGTH = BYTE_LENGTH + CHECKSUM_SIZE

    @staticmethod
    def is_address(s: str):
        identity_bytes = base58.b58decode(s)

        if len(identity_bytes) != Address.DISPLAY_BYTE_LENGTH:
            return False

        # split the identity into address and checksum
        address_raw = identity_bytes[:Address.BYTE_LENGTH]
        checksum = identity_bytes[Address.BYTE_LENGTH:]

        # calculate the expected checksum
        expected_checksum = Address._calculate_checksum(address_raw)

        if checksum != expected_checksum:
            return False

        return True


    def __init__(self, identity):
        if isinstance(identity, Address):
            self._address = identity._address
            self._display = identity._display

        elif isinstance(identity, Identity):
            self._address = Address._digest(identity.public_key_bytes)
            self._display = self._calculate_display(self._address)

        elif isinstance(identity, bytes):
            if len(identity) != self.BYTE_LENGTH:
                raise RuntimeError('Incorrect length of binary address, expected {}, received {}'
                                   .format(self.BYTE_LENGTH, len(identity)))

            self._address = identity
            self._display = self._calculate_display(self._address)

        elif isinstance(identity, str):

            if not Address.is_address(identity):
                raise RuntimeError('Invalid Address')

            # split the identity into address and checksum
            address_raw = base58.b58decode(identity)[:self.BYTE_LENGTH]
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
        if other is None:
            return False
        return bytes(self) == bytes(other)

    def to_hex(self):
        return self._address.hex()

    @staticmethod
    def _digest(data):
        return sha256_hash(data)

    @staticmethod
    def _calculate_checksum(address_raw):
        return Address._digest(address_raw)[:Address.CHECKSUM_SIZE]

    @classmethod
    def _calculate_display(cls, address_raw):
        return base58.b58encode(address_raw + Address._digest(address_raw)[:cls.CHECKSUM_SIZE]).decode()
