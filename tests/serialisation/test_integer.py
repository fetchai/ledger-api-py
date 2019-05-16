import io

from fetchai.ledger.serialisation.integer import encode, decode
from .common import SerialisationUnitTest


class IntegerSerialisationTests(SerialisationUnitTest):
    def test_small_unsigned_encode(self):
        buffer = io.BytesIO()
        encode(buffer, 4)
        self.assertIsEncoded(buffer, '04')

    def test_small_signed_encode(self):
        buffer = io.BytesIO()
        encode(buffer, -4)
        self.assertIsEncoded(buffer, 'E4')

    def test_1byte_unsigned_encode(self):
        buffer = io.BytesIO()
        encode(buffer, 0x80)
        self.assertIsEncoded(buffer, 'C080')

    def test_2byte_unsigned_encode(self):
        buffer = io.BytesIO()
        encode(buffer, 0xEDEF)
        self.assertIsEncoded(buffer, 'C1EDEF')

    def test_4byte_unsigned_encode(self):
        buffer = io.BytesIO()
        encode(buffer, 0xEDEFABCD)
        self.assertIsEncoded(buffer, 'C2EDEFABCD')

    def test_8byte_unsigned_encode(self):
        buffer = io.BytesIO()
        encode(buffer, 0xEDEFABCD01234567)
        self.assertIsEncoded(buffer, 'C3EDEFABCD01234567')

    def test_1byte_signed_encode(self):
        buffer = io.BytesIO()
        encode(buffer, -0x80)
        self.assertIsEncoded(buffer, 'D080')

    def test_2byte_signed_encode(self):
        buffer = io.BytesIO()
        encode(buffer, -0xEDEF)
        self.assertIsEncoded(buffer, 'D1EDEF')

    def test_4byte_signed_encode(self):
        buffer = io.BytesIO()
        encode(buffer, -0xEDEFABCD)
        self.assertIsEncoded(buffer, 'D2EDEFABCD')

    def test_8byte_signed_encode(self):
        buffer = io.BytesIO()
        encode(buffer, -0xEDEFABCD01234567)
        self.assertIsEncoded(buffer, 'D3EDEFABCD01234567')

    # Decode counter parts

    def test_small_unsigned_decode(self):
        encoded = self._from_hex('04')
        self.assertEqual(decode(encoded), 4)

    def test_small_signed_decode(self):
        encoded = self._from_hex('E4')
        self.assertEqual(decode(encoded), -4)

    def test_1byte_unsigned_decode(self):
        encoded = self._from_hex('C080')
        self.assertEqual(decode(encoded), 0x80)

    def test_2byte_unsigned_decode(self):
        encoded = self._from_hex('C1EDEF')
        self.assertEqual(decode(encoded), 0xEDEF)

    def test_4byte_unsigned_decode(self):
        encoded = self._from_hex('C2EDEFABCD')
        self.assertEqual(decode(encoded), 0xEDEFABCD)

    def test_8byte_unsigned_decode(self):
        encoded = self._from_hex('C3EDEFABCD01234567')
        self.assertEqual(decode(encoded), 0xEDEFABCD01234567)

    def test_1byte_signed_decode(self):
        encoded = self._from_hex('D080')
        self.assertEqual(decode(encoded), -0x80)

    def test_2byte_signed_decode(self):
        encoded = self._from_hex('D1EDEF')
        self.assertEqual(decode(encoded), -0xEDEF)

    def test_4byte_signed_decode(self):
        encoded = self._from_hex('D2EDEFABCD')
        self.assertEqual(decode(encoded), -0xEDEFABCD)

    def test_8byte_signed_decode(self):
        encoded = self._from_hex('D3EDEFABCD01234567')
        self.assertEqual(decode(encoded), -0xEDEFABCD01234567)

    # Error cases

    def test_invalid_large_integer(self):
        too_big = 1 << 64
        buffer = io.BytesIO()
        with self.assertRaises(RuntimeError):
            encode(buffer, too_big)
