import base64
import unittest
from io import StringIO
from unittest.mock import patch

import ecdsa

from fetchai.ledger.crypto.entity import Entity

SUPER_SECURE_PASSWORD = "F3tch.A1 t0 th3 Moon!!!1"
WEAK_PASSWORD = 'password'


class EntityTests(unittest.TestCase):
    def test_generation(self):
        entity = Entity()

        self.assertEqual(32, len(entity.private_key_bytes))

        # check the other binary representations
        self.assertEqual(base64.b64encode(entity.private_key_bytes).decode(), entity.private_key)
        self.assertEqual(entity.private_key_bytes.hex(), entity.private_key_hex)

        signing_key = ecdsa.SigningKey.from_string(entity.private_key_bytes, curve=Entity.curve,
                                                   hashfunc=Entity.hash_function)
        verifying_key = signing_key.get_verifying_key()

        self.assertEqual(verifying_key.to_string(), entity.public_key_bytes)

        # check the other binary representations
        self.assertEqual(base64.b64encode(entity.public_key_bytes).decode(), entity.public_key)
        self.assertEqual(entity.public_key_bytes.hex(), entity.public_key_hex)

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

    def test_loads(self):
        ref = Entity()
        value = ref.dumps(SUPER_SECURE_PASSWORD)
        other = Entity.loads(value, SUPER_SECURE_PASSWORD)
        self.assertEqual(ref.private_key, other.private_key)

    def test_load(self):
        ref = Entity()
        stream = StringIO(ref.dumps(SUPER_SECURE_PASSWORD))
        other = Entity.load(stream, SUPER_SECURE_PASSWORD)
        self.assertEqual(ref.private_key, other.private_key)

    def test_dumps(self):
        ref = Entity()
        stream = StringIO()
        ref.dump(stream, SUPER_SECURE_PASSWORD)
        stream.seek(0)
        other = Entity.load(stream, SUPER_SECURE_PASSWORD)
        self.assertEqual(ref.private_key, other.private_key)

    def test_dump_failure_on_weak_password(self):
        stream = StringIO()
        with self.assertRaises(RuntimeError):
            Entity().dump(stream, WEAK_PASSWORD)

    def test_dumps_failure_on_weak_password(self):
        with self.assertRaises(RuntimeError):
            Entity().dumps(WEAK_PASSWORD)

    def test_conversion_from_hex(self):
        ref = Entity()
        other = Entity.from_hex(ref.private_key_hex)
        self.assertEqual(ref.private_key, other.private_key)

    def test_prompt_load(self):
        ref = Entity()
        stream = StringIO()

        # write the entity to the stream
        ref.dump(stream, SUPER_SECURE_PASSWORD)

        # reset the stream
        stream.seek(0)
        with patch('getpass.getpass') as mock_getpass:
            mock_getpass.side_effect = [SUPER_SECURE_PASSWORD]

            other = Entity.prompt_load(stream)
            self.assertEqual(other.private_key, ref.private_key)

    def test_prompt_dump(self):
        ref = Entity()

        stream = StringIO()
        with patch('getpass.getpass') as mock_getpass:
            mock_getpass.side_effect = [WEAK_PASSWORD, SUPER_SECURE_PASSWORD, WEAK_PASSWORD, SUPER_SECURE_PASSWORD]
            ref.prompt_dump(stream)

        stream.seek(0)
