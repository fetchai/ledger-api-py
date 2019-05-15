import hashlib
import unittest

import base58

from fetchai.ledger.crypto.address import Address
from fetchai.ledger.crypto.entity import Entity


def _calc_digest(data):
    hash_func = hashlib.sha256()
    hash_func.update(data)
    return hash_func.digest()


def _calc_address(public_key_bytes):
    bytes = _calc_digest(public_key_bytes)
    display_bytes = bytes + _calc_digest(bytes)[:4]
    display = base58.b58encode(display_bytes).decode()
    return bytes, display


class AddressTests(unittest.TestCase):
    def test_construction_from_identity(self):
        entity = Entity()
        address = Address(entity)

        # manually compute the address value
        expected_address_bytes, expected_display = _calc_address(entity.public_key_bytes)

        self.assertEqual(expected_address_bytes, bytes(address))
        self.assertEqual(expected_display, str(address))

    def test_construction_from_bytes(self):
        dummy_address = bytes(list(range(32)))
        address = Address(dummy_address)

        self.assertEqual(dummy_address, bytes(address))

    def test_construction_from_string(self):
        entity = Entity()

        # manually compute the address value
        expected_address_bytes, expected_display = _calc_address(entity.public_key_bytes)

        # re-create the address from the display string
        address = Address(expected_display)

        self.assertEqual(bytes(address), expected_address_bytes)
        self.assertEqual(str(address), expected_display)

    def test_construction_from_address(self):
        entity = Entity()
        address1 = Address(entity)
        address2 = Address(address1)

        self.assertEqual(bytes(address1), bytes(address2))
