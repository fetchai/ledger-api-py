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
    def is_address(address: str) -> bool:
        raw_address = base58.b58decode(address)

        if len(raw_address) != Address.DISPLAY_BYTE_LENGTH:
            return False

        # split the identity into address and checksum
        address_raw = raw_address[:Address.BYTE_LENGTH]
        checksum = raw_address[Address.BYTE_LENGTH:]

        # calculate the expected checksum
        expected_checksum = Address._calculate_checksum(address_raw)

        if checksum != expected_checksum:
            return False

        return True

    def __init__(self, value):
        if isinstance(value, Address):
            self._address = value._address
            self._display = value._display

        elif isinstance(value, Identity):
            self._address = Address._digest(value.public_key_bytes)
            self._display = self._calculate_display(self._address)

        elif isinstance(value, bytes):
            if len(value) != self.BYTE_LENGTH:
                raise ValueError('Incorrect length of binary address, expected {}, received {}'
                                 .format(self.BYTE_LENGTH, len(value)))

            self._address = value
            self._display = self._calculate_display(self._address)

        elif isinstance(value, str):
            if not Address.is_address(value):
                raise ValueError('Invalid Address')

            # split the identity into address and checksum
            address_raw = base58.b58decode(value)[:self.BYTE_LENGTH]
            # update internals
            self._address = address_raw
            self._display = value

        else:
            raise ValueError('Unknown address value type')

    def __str__(self):
        return self._display

    def __bytes__(self):
        return self._address

    def __hash__(self):
        return hash(self._address)

    def __eq__(self, other: 'Address'):
        if isinstance(other, Address):
            return self._address == other._address
        return False

    def __ne__(self, other: 'Address'):
        return not (self == other)

    @staticmethod
    def _digest(data):
        return sha256_hash(data)

    @staticmethod
    def _calculate_checksum(address_raw):
        return Address._digest(address_raw)[:Address.CHECKSUM_SIZE]

    @classmethod
    def _calculate_display(cls, address_raw):
        return base58.b58encode(address_raw + Address._digest(address_raw)[:cls.CHECKSUM_SIZE]).decode()
