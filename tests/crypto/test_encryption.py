import json
from unittest import TestCase
from unittest.mock import patch

from fetchai.ledger.crypto import Entity
from fetchai.ledger.crypto import entity


class EncryptionTests(TestCase):
    def test_encrypt_decrypt(self):
        """Check that plaintext is recoverable from encrypted data"""
        password = 'abcdABCD1234##'
        plaintext = 'plaintext'

        encrypted, n, iv, salt = entity._encrypt(password, plaintext.encode())

        self.assertEqual(n, len(plaintext))

        decrypted = entity._decrypt(password, salt, encrypted, n, iv)

        self.assertEqual(decrypted.decode(), plaintext)

    def test_to_from_json(self):
        """Check json save schema allows successful recovery of private key"""
        ent1 = entity.Entity()
        password = 'abcdABCD1234##'
        json_obj = ent1._to_json_object(password)

        # Test conversion of dict object to/from json (to ensure serializability)
        json_str = json.dumps(json_obj)
        json_obj2 = json.loads(json_str)
        self.assertEqual(json_obj2, json_obj)

        ent2 = entity.Entity._from_json_object(json_obj2, password)

        self.assertEqual(ent1.private_key, ent2.private_key)

    def test_invalid_password(self):
        ent1 = entity.Entity()
        password = 'abcdABCD1234##'
        json = ent1._to_json_object(password)

        ent2 = entity.Entity._from_json_object(json, 'invalid_password')
        self.assertNotEqual(ent1.private_key, ent2.private_key)

    @patch('logging.warning')
    def test_strong_password(self, mock_warning):
        """Check that we reject weak passwords based on length and character types"""
        # Passwords should require:
        #  14 characters
        #  one or more lower case letters
        #  one or more upper case letters
        #  one or more digits
        #  one or more symbols
        self.assertTrue(Entity.is_strong_password('a1A_aaaaaaaaaa'), "Valid password failed")

        self.assertFalse(Entity.is_strong_password('abc'), "Short password passed")
        self.assertFalse(Entity.is_strong_password('aaaaaaaaaaaaaa'), "All lower case passed")
        self.assertFalse(Entity.is_strong_password('11111111111111'), "All numbers passed")
        self.assertFalse(Entity.is_strong_password('AAAAAAAAAAAAAA'), "All upper case passed")
        self.assertFalse(Entity.is_strong_password('______________'), "All symbols passed")

        self.assertFalse(Entity.is_strong_password('a1Aaaaaaaaaaaa'), "No symbol passed")
        self.assertFalse(Entity.is_strong_password('a1a_aaaaaaaaaa'), "No upper case passed")
        self.assertFalse(Entity.is_strong_password('aaA_aaaaaaaaaa'), "No number passed")
        self.assertFalse(Entity.is_strong_password('A1_AAAAAAAAAAA'), "No lower case passed")
