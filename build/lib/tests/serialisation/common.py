import binascii
import io
import unittest
from typing import Union


class SerialisationUnitTest(unittest.TestCase):
    def assertIsEncoded(self, encoded: Union[bytes, io.BytesIO], expected_hex: str):
        if isinstance(encoded, io.BytesIO):
            data_bytes = encoded.getvalue()
        elif isinstance(encoded, bytes):
            data_bytes = encoded
        else:
            assert False  # knwo

        self.assertEqual(binascii.hexlify(data_bytes).decode().lower(), expected_hex.lower())

    @classmethod
    def _from_bytes(cls, data_bytes: bytes):
        return io.BytesIO(data_bytes)

    @classmethod
    def _from_hex(cls, data_hex: str):
        return cls._from_bytes(binascii.unhexlify(data_hex))
