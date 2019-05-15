import io

from fetchai.ledger.crypto import Entity, Identity
from fetchai.ledger.serialisation.identity import encode, decode
from .common import SerialisationUnitTest


class IdentitySerialisationTests(SerialisationUnitTest):
    def test_encode(self):
        entity = Entity()

        expected_encoding = bytes([0x04]) + entity.public_key_bytes

        buffer = io.BytesIO()
        encode(buffer, entity)

        encoded_identity = buffer.getvalue()

        self.assertEqual(encoded_identity, expected_encoding)

    def test_decode(self):
        entity = Entity()

        expected_encoding = bytes([0x04]) + entity.public_key_bytes

        buffer = io.BytesIO(expected_encoding)
        identity = decode(buffer)

        self.assertEqual(identity, entity)




