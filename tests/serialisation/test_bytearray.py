import io

from fetchai.ledger.serialisation.bytearray import encode, decode
from .common import SerialisationUnitTest


class ByteArraySerialisationTests(SerialisationUnitTest):
    def test_encode(self):
        data = bytes(list(range(10)))

        # encode the address
        buffer = io.BytesIO()
        encode(buffer, data)

        self.assertIsEncoded(buffer, '0A00010203040506070809')

    def test_decode(self):
        encoded_stream = self._from_hex('0A00010203040506070809')

        # decode the address
        data = decode(encoded_stream)

        self.assertIsEncoded(data, '00010203040506070809')
