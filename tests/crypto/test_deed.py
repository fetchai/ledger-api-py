from unittest import TestCase
from unittest.mock import patch

from fetchai.ledger.crypto import Entity, Address
from fetchai.ledger.crypto.deed import Deed, Operation, InvalidDeedError


class DeedTests(TestCase):
    def setUp(self) -> None:
        self.entity = Entity()
        self.address = Address(self.entity)
        self.board = [Entity() for _ in range(4)]

    def test_create(self):
        """Test correct creation of deed"""
        deed = Deed()

        for signee in self.board:
            deed.set_signee(signee, 1)

        deed.set_threshold(Operation.amend, 3)

        self.assertEqual(deed.total_votes, 4)
        self.assertEqual(deed.get_threshold(Operation.amend), 3)
        for signee in self.board:
            self.assertEqual(deed.get_signee(signee), 1)
        deed.is_sane(throw=True)

    def test_threshold_sanity(self):

        """Test that thresholds can be correctly set"""
        deed = Deed()

        # Add signees with total voting weight of 5
        deed.set_signee(self.board[0], 2)
        deed.set_signee(self.board[1], 2)
        deed.set_signee(self.board[2], 1)

        deed.set_threshold(Operation.transfer, deed.total_votes + 1)
        # Setting any threshold higher than the voting weight should fail
        with self.assertRaises(InvalidDeedError):
            deed.is_sane(throw=True)

        # Check threshold successfully set
        deed.set_threshold(Operation.amend, deed.total_votes)
        deed.set_threshold(Operation.transfer, deed.total_votes - 1)
        deed.is_sane(throw=True)

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
        deed.set_threshold(Operation.transfer, 1)

        # Attempting to create un-amendable deed without explicitly requesting it is an error
        with self.assertRaises(InvalidDeedError):
            deed.is_sane(throw=True)

        # Attempting to create un-amendable deed without explicitly requesting it is an error
        with self.assertRaises(InvalidDeedError):
            deed.deed_creation_json()

    def test_allow_missing_amend_threshold(self):
        """Checks successful deed operation if amend threshold is missing, but explicit permission has been granted"""
        deed = Deed(allow_no_amend=True)
        deed.set_signee(self.board[0], 1)
        deed.set_threshold(Operation.transfer, 1)

        # With explicit request, this should still be a warning
        with patch('logging.warning') as mock_warn:
            deed.is_sane(throw=True)
            self.assertEqual(mock_warn.call_count, 1)

        # With explicit request, this should still be a warning
        with patch('logging.warning') as mock_warn:
            json = deed.deed_creation_json()
            self.assertEqual(mock_warn.call_count, 1)

        json = deed.deed_creation_json()
        thresholds = json['thresholds']
        self.assertNotIn(str(Operation.amend), thresholds)
        self.assertIn(str(Operation.transfer), thresholds)
