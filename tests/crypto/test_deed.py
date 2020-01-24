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

        deed.amend_threshold = 3

        self.assertEqual(deed.total_votes, 4)
        self.assertEqual(deed.return_threshold(Operation.amend), 3)
        self.assertEqual(deed.amend_threshold, 3)

        self.assertEqual(deed._signees, {s: 1 for s in self.board})
        self.assertEqual(deed._thresholds, {'amend': 3})

    def test_thresholds(self):
        """Test that thresholds can be correctly set"""
        deed = Deed()

        # Add signees with total voting weight of 5
        deed.set_signee(self.board[0], 2)
        deed.set_signee(self.board[1], 2)
        deed.set_signee(self.board[2], 1)

        # Setting any threshold higher than the voting weight should fail
        with self.assertRaises(InvalidDeedError):
            deed.set_threshold(Operation.transfer, deed.total_votes + 1)

        # Check threshold successfully set
        deed.set_threshold(Operation.transfer, deed.total_votes - 1)
        deed.set_threshold(Operation.amend, deed.total_votes)

        json = deed.deed_creation_json()
        self.assertEqual(json['thresholds']['amend'], 5)
        self.assertEqual(json['thresholds']['transfer'], 4)

    def test_enum(self):
        self.assertEqual(str(Operation.amend), 'amend')
        self.assertEqual(str(Operation.transfer), 'transfer')
        self.assertEqual(str(Operation.execute), 'execute')
        self.assertEqual(str(Operation.stake), 'stake')
        self.assertEqual(repr(Operation.amend), '<Operation.amend>')
        self.assertEqual(repr(Operation.transfer), '<Operation.transfer>')
        self.assertEqual(repr(Operation.execute), '<Operation.execute>')
        self.assertEqual(repr(Operation.stake), '<Operation.stake>')

    def test_warn_on_no_amend_threshold(self):
        """Checks a warning is printed when creating a deed with no amend threshold"""
        deed = Deed()

        # Add signees with total voting weight of 5
        deed.set_signee(self.board[0], 2)
        deed.set_signee(self.board[1], 2)
        deed.set_signee(self.board[2], 1)

        # Attempting to create un-amendable deed without explicitly requesting it is an error
        with self.assertRaises(InvalidDeedError):
            deed.deed_creation_json(allow_no_amend=False)

        # With explicit request, this should still be a warning
        with patch('logging.warning') as mock_warn:
            json = deed.deed_creation_json(allow_no_amend=True)
            self.assertEqual(mock_warn.call_count, 1)

        self.assertEqual(json['thresholds'], {})

        # Adding an amend threshold greater than the available voting power should cause error
        deed._thresholds['amend'] = deed.total_votes + 1
        with self.assertRaises(InvalidDeedError):
            json = deed.deed_creation_json()

        # Adding an amend threshold lower than the available votes shouldn't cause a warning or error
        deed.amend_threshold = deed.total_votes - 1
        with patch('logging.warning') as mock_warn:
            json = deed.deed_creation_json()
            self.assertEqual(mock_warn.call_count, 0)
