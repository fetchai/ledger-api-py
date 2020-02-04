import unittest

from fetchai.ledger.api.tx import TxStatus


class TransactionStatusObjTests(unittest.TestCase):
    def setUp(self) -> None:
        self.digest = bytes(range(32))
        self.status = TxStatus(self.digest, 'Executed', 200, 12, 1233, 32323)

    def test_basic_properties(self):
        self.assertEqual(self.status.status, 'Executed')
        self.assertEqual(self.status.exit_code, 200)
        self.assertEqual(self.status.charge_limit, 12)
        self.assertEqual(self.status.charge_rate, 1233)
        self.assertEqual(self.status.fee, 32323)
        self.assertEqual(self.status.digest_hex, '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f')
        self.assertEqual(self.status.digest, '0x000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f')
        self.assertEqual(self.status.digest_bytes, self.digest)
        self.assertTrue(self.status.successful)
        self.assertFalse(self.status.failed)
        self.assertFalse(self.status.non_terminal)

    def test_unknown_status(self):
        self.status.status = 'Unknown'
        self.assertFalse(self.status.successful)
        self.assertFalse(self.status.failed)
        self.assertTrue(self.status.non_terminal)

    def test_pending_status(self):
        self.status.status = 'Pending'
        self.assertFalse(self.status.successful)
        self.assertFalse(self.status.failed)
        self.assertTrue(self.status.non_terminal)

    def test_submitted_status(self):
        self.status.status = 'Submitted'
        self.assertTrue(self.status.successful)
        self.assertFalse(self.status.failed)
        self.assertFalse(self.status.non_terminal)

    def test_failed_status(self):
        self.status.status = 'Contract Execution Failure'
        self.assertFalse(self.status.successful)
        self.assertTrue(self.status.failed)
        self.assertFalse(self.status.non_terminal)
