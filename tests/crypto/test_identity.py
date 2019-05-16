import unittest

from fetchai.ledger.crypto.entity import Entity
from fetchai.ledger.crypto.identity import Identity


class IdentityTests(unittest.TestCase):
    def test_construction_from_verifying_key(self):
        entity = Entity()  # create a private / public key pair

        # create the identity from the identity (copy)
        identity = Identity(entity.verifying_key)

        # ensure the they are the same
        self.assertEqual(identity.public_key_bytes, entity.public_key_bytes)

    def test_construction_from_bytes(self):
        entity = Entity()  # create a private / public key pair

        # create the identity from the identity (copy)
        identity = Identity(entity.public_key_bytes)

        # ensure the they are the same
        self.assertEqual(identity.public_key_bytes, entity.public_key_bytes)

    def test_construction_from_identity(self):
        entity = Entity()  # create a private / public key pair
        identity = Identity(entity)

        self.assertEqual(entity.public_key_bytes, identity.public_key_bytes)

    def test_supports_collections(self):
        entity = Entity()

        # create a series of identities
        identity1 = Identity(entity)
        identity2 = Identity(entity)
        identity3 = Identity(identity2)

        identity_list = [identity1, identity2, identity3]
        self.assertEqual(len(identity_list), 3)
        self.assertIn(identity1, identity_list)
        self.assertIn(identity2, identity_list)
        self.assertIn(identity3, identity_list)

        # due to the fact that each identity is the name, the first element will always be matched
        self.assertEqual(identity_list.index(identity1), 0)
        self.assertEqual(identity_list.index(identity2), 0)
        self.assertEqual(identity_list.index(identity3), 0)

        identity_set = set(identity_list)
        self.assertEqual(len(identity_set), 1)
        self.assertIn(identity1, identity_set)
        self.assertIn(identity2, identity_set)
        self.assertIn(identity3, identity_set)

    def test_not_equal(self):
        entity1 = Entity()
        entity2 = Entity()
        self.assertNotEqual(entity1, entity2)

    def test_invalid_contrstruction(self):
        with self.assertRaises(RuntimeError):
            _ = Identity(str())

    def test_construction_from_strings(self):
        ref = Entity()

        test1 = Identity.from_hex(ref.public_key_hex)
        self.assertEqual(ref, test1)

        test2 = Identity.from_base64(ref.public_key)
        self.assertEqual(ref, test2)
