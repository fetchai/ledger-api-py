import base64
import binascii
import unittest

import ecdsa

from fetchai.ledger.crypto.entity import Entity


class EntityTests(unittest.TestCase):
    def test_generation(self):
        entity = Entity()

        self.assertEqual(32, len(entity.private_key_bytes))

        # check the other binary representations
        self.assertEqual(base64.b64encode(entity.private_key_bytes).decode(), entity.private_key)
        self.assertEqual(binascii.hexlify(entity.private_key_bytes).decode(), entity.private_key_hex)

        signing_key = ecdsa.SigningKey.from_string(entity.private_key_bytes, curve=Entity.curve,
                                                   hashfunc=Entity.hash_function)
        verifying_key = signing_key.get_verifying_key()

        self.assertEqual(verifying_key.to_string(), entity.public_key_bytes)

        # check the other binary representations
        self.assertEqual(base64.b64encode(entity.public_key_bytes).decode(), entity.public_key)
        self.assertEqual(binascii.hexlify(entity.public_key_bytes).decode(), entity.public_key_hex)

    def test_construction_from_bytes(self):
        # create a reference and a copy of the entity
        reference = Entity()
        other = Entity(reference.private_key_bytes)

        self.assertEqual(reference.private_key_bytes, other.private_key_bytes)
        self.assertEqual(reference.private_key, other.private_key)
        self.assertEqual(reference.private_key_hex, other.private_key_hex)

        self.assertEqual(reference.public_key_bytes, other.public_key_bytes)
        self.assertEqual(reference.public_key, other.public_key)
        self.assertEqual(reference.public_key_hex, other.public_key_hex)

    def test_signing_verifying_cycle(self):
        entity = Entity()

        payload = 'foo bar is a baz'

        # sign the payload
        signature = entity.sign(payload.encode())

        # verify the payload
        self.assertTrue(entity.verify(payload.encode(), signature))

        # modify the signature slightly
        bad_signature = bytes([(signature[0] + 1) & 0xff]) + signature[1:]

        self.assertFalse(entity.verify(payload.encode(), bad_signature))

        # also ensure a different payload is not verifiable
        self.assertFalse(entity.verify('foo bar is not a baz'.encode(), signature))

    def test_construction_from_base64(self):
        ref = Entity()
        ref_key = ref.private_key

        other = Entity.from_base64(ref_key)
        self.assertEqual(ref.private_key_bytes, other.private_key_bytes)

    def test_invalid_construction(self):
        with self.assertRaises(RuntimeError):
            _ = Entity(str())

    def test_signing_key(self):
        entity = Entity()
        self.assertIsInstance(entity.signing_key, ecdsa.SigningKey)
