import unittest

from fetchai.ledger.decode import decode_hex_or_b64


class UniversalDecodeTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(decode_hex_or_b64(''), b'')
        self.assertEqual(decode_hex_or_b64(b''), b'')

    def test_unprefixed_hex(self):
        self.assertEqual(decode_hex_or_b64('deadbeef'), b'\xde\xad\xbe\xef')
        self.assertEqual(decode_hex_or_b64(b'deadbeef'), b'\xde\xad\xbe\xef')

    def test_prefixed_hex(self):
        self.assertEqual(decode_hex_or_b64('0xdeadbeef'), b'\xde\xad\xbe\xef')
        self.assertEqual(decode_hex_or_b64(b'0xdeadbeef'), b'\xde\xad\xbe\xef')

    def test_padded_base64(self):
        self.assertEqual(decode_hex_or_b64('YWJjZDEyMzQ='), b'abcd1234')
        self.assertEqual(decode_hex_or_b64(b'YWJjZDEyMzQ='), b'abcd1234')

    def test_unpadded_base64(self):
        self.assertEqual(decode_hex_or_b64('YWJjZDEyMzQ'), b'abcd1234')
        self.assertEqual(decode_hex_or_b64(b'YWJjZDEyMzQ'), b'abcd1234')

    def test_0x(self):
        self.assertEqual(decode_hex_or_b64('0x'), b'\xd3')
        self.assertEqual(decode_hex_or_b64(b'0x'), b'\xd3')

    def test_invalid_decode_type(self):
        with self.assertRaises(TypeError):
            decode_hex_or_b64(4)
