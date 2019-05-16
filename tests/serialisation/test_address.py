import io

from fetchai.ledger.crypto import Address
from fetchai.ledger.serialisation.address import encode, decode
from .common import SerialisationUnitTest


class AddressSerialisationTests(SerialisationUnitTest):
    def test_encode(self):
        dummy_raw_address = bytes(list(range(Address.BYTE_LENGTH)))
        dummy_address = Address(dummy_raw_address)

        # encode the address
        buffer = io.BytesIO()
        encode(buffer, dummy_address)

        self.assertEqual(bytes(dummy_address), buffer.getvalue())
        self.assertIsEncoded(buffer.getvalue(), '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f')

    def test_decode(self):
        expected_raw_address = bytes(list(range(Address.BYTE_LENGTH)))

        # decode the address
        encoded_address = self._from_bytes(expected_raw_address)
        address = decode(encoded_address)

        # ensure it matches our expectations
        self.assertEqual(bytes(address), expected_raw_address)
