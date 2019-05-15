import unittest

from fetchai.ledger.bitvector import BitVector


class BitVectorSerialisationTests(unittest.TestCase):
    def test_empty(self):
        bits = BitVector()

        self.assertEqual(len(bits), 0)
        self.assertEqual(bits.byte_length, 0)

    def test_sets(self):
        bits = BitVector(8)
        bits.set(3, 1)
        bits.set(6, 1)
        bits.set(7, 1)

        self.assertEqual(len(bits), 8)
        self.assertEqual(bits.byte_length, 1)
        self.assertEqual(bits.as_hex(), 'c8')

    def test_gets(self):
        bits = BitVector.from_hex_string('c8')

        self.assertEqual(bits.get(0), 0)
        self.assertEqual(bits.get(1), 0)
        self.assertEqual(bits.get(2), 0)
        self.assertEqual(bits.get(3), 1)
        self.assertEqual(bits.get(4), 0)
        self.assertEqual(bits.get(5), 0)
        self.assertEqual(bits.get(6), 1)
        self.assertEqual(bits.get(7), 1)
