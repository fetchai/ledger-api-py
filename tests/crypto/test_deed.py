import json
from unittest import TestCase
from unittest.mock import patch

from fetchai.ledger.crypto import Entity, Address
from fetchai.ledger.crypto.deed import Deed, Operation, InvalidDeedError


class DeedTests(TestCase):
    def setUp(self) -> None:
        self.entity = Entity()
        self.address = Address(self.entity)
        self.board = [Entity() for _ in range(4)]

    def create_default_deed(self):
        deed = Deed()

        # Add signees with total voting weight of 5
        for signee in self.board:
            deed.set_signee(signee, 1)

        deed.set_operation(Operation.amend, deed.total_votes)
        deed.set_operation(Operation.transfer, deed.total_votes - 1)

        return deed

    def test_create(self):
        """Test correct creation of deed"""
        deed = Deed()

        for signee in self.board:
            deed.set_signee(signee, 1)

        deed.set_operation(Operation.amend, 3)

        self.assertEqual(deed.total_votes, 4)
        self.assertEqual(deed.get_threshold(Operation.amend), 3)
        for signee in self.board:
            self.assertEqual(deed.get_signee(signee), 1)

    def test_total_voting_weight(self):
        deed = Deed()

        v = 0
        expected_total_voting_weight = 0
        for signee in self.board:
            v += 1
            expected_total_voting_weight += v
            deed.set_signee(signee, v)

        self.assertEqual(deed.total_votes, expected_total_voting_weight)

    def test_threshold_sanity(self):
        """Test that thresholds can be correctly set"""
        deed = Deed()

        # Add signees with total voting weight of 5
        deed.set_signee(self.board[0], 2)
        deed.set_signee(self.board[1], 2)
        deed.set_signee(self.board[2], 1)
        deed.set_operation(Operation.amend, 5)
        deed.validate()

        deed.set_operation(Operation.transfer, 5 + 1)
        # Setting any threshold higher than the voting weight should fail
        with self.assertRaises(InvalidDeedError):
            deed.validate()

        # Check threshold successfully set
        deed.set_operation(Operation.transfer, 5 - 1)
        deed.validate()

        self.assertEqual(deed.get_threshold(Operation.amend), 5)
        self.assertEqual(deed.get_threshold(Operation.transfer), 4)

    def test_enum(self):
        self.assertEqual(str(Operation.amend), 'amend')
        self.assertEqual(str(Operation.transfer), 'transfer')
        self.assertEqual(str(Operation.execute), 'execute')
        self.assertEqual(str(Operation.stake), 'stake')
        self.assertEqual(repr(Operation.amend), '<Operation.amend>')
        self.assertEqual(repr(Operation.transfer), '<Operation.transfer>')
        self.assertEqual(repr(Operation.execute), '<Operation.execute>')
        self.assertEqual(repr(Operation.stake), '<Operation.stake>')

    def test_warn_on_missing_amend_threshold(self):
        """Checks a warning is printed when creating a deed when amend threshold is specified"""
        deed = Deed()
        deed.set_signee(self.board[0], 1)
        deed.set_operation(Operation.transfer, 1)

        # Attempting to create un-amendable deed without explicitly requesting it is an error
        with self.assertRaises(InvalidDeedError):
            deed.validate()

        # Attempting to create un-amendable deed without explicitly requesting it is an error
        with self.assertRaises(InvalidDeedError):
            deed.to_json()

    def test_allow_missing_amend_threshold(self):
        """Checks successful deed operation if amend threshold is missing, but explicit permission has been granted"""
        deed = Deed()
        deed.set_signee(self.board[0], 1)
        deed.set_operation(Operation.transfer, 1)
        deed.require_amend = False

        # With explicit request, this should still be a warning
        with patch('logging.warning') as mock_warn:
            deed.validate()
            self.assertEqual(mock_warn.call_count, 1)

        # With explicit request, this should still be a warning
        with patch('logging.warning') as mock_warn:
            obj = deed.to_json()
            self.assertEqual(mock_warn.call_count, 1)

        thresholds = obj['thresholds']
        self.assertNotIn(str(Operation.amend), thresholds)
        self.assertIn(str(Operation.transfer), thresholds)

    def test_comparison_operator(self):
        """Test creation from obj - primary workflow"""
        deed = self.create_default_deed()
        deed_copy = self.create_default_deed()

        # TEST OBJECTIVE:
        self.assertEqual(deed, deed_copy)

    def test_to_json(self):
        """Test creation from obj - primary workflow"""
        deed = self.create_default_deed()
        obj = deed.to_json()

        expected_signees_count = 0
        json_signees = obj['signees']
        for signer, voting_weight in deed.votes:
            self.assertEqual(json_signees[str(signer)], voting_weight)
            expected_signees_count += 1

        self.assertEqual(expected_signees_count, len(json_signees))

        expected_thresholds_count = 0
        json_thresholds = obj['thresholds']
        for operation, threshold in deed.thresholds:
            self.assertEqual(json_thresholds[str(operation)], threshold)
            expected_thresholds_count += 1

        self.assertEqual(expected_thresholds_count, len(json_thresholds))

    def test_from_json(self):
        """Test creation from obj - promary workflow"""
        deed = self.create_default_deed()
        obj = deed.to_json()
        deed_reconstituted = Deed.from_json(obj)
        self.assertEqual(deed, deed_reconstituted)

    def test_from_json_string(self):
        deed = self.create_default_deed()
        obj = deed.to_json()
        deed_reconstituted = Deed.from_json(json.dumps(obj))
        self.assertEqual(deed, deed_reconstituted)

    def test_equality(self):
        deed = self.create_default_deed()
        other = self.create_default_deed()
        self.assertEqual(deed, deed)
        self.assertEqual(deed, other)

    def test_inequality(self):
        deed = Deed()
        other = self.create_default_deed()
        other.set_operation(Operation.amend, 1)

        self.assertTrue(deed != other)

    def test_drop_signee(self):
        deed = Deed()
        deed.set_signee(self.address, 10)

        self.assertIn(Address(self.address), deed.signees)
        deed.remove_signee(self.address)
        self.assertNotIn(Address(self.address), deed.signees)

    def test_remove_operation(self):
        deed = self.create_default_deed()
        self.assertIn(Operation.amend, deed.operations)
        deed.remove_operation(Operation.amend)
        self.assertNotIn(Operation.amend, deed.operations)

    def test_setting_invalid_weight(self):
        deed = Deed()
        with self.assertRaises(ValueError):
            deed.set_signee(self.address, -10)

    def test_setting_invalid_threshold(self):
        deed = Deed()
        with self.assertRaises(ValueError):
            deed.set_operation(Operation.transfer, -2)
