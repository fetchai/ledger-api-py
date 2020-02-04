from typing import IO

from fetchai.ledger.crypto import Identity

UNCOMPRESSED_SCEP256K1_PUBLIC_KEY = 0x04
UNCOMPRESSED_SCEP256K1_PUBLIC_KEY_LEN = 64


def decode(stream: IO[bytes]) -> Identity:
    header = stream.read(1)[0]

    if UNCOMPRESSED_SCEP256K1_PUBLIC_KEY == header:
        public_key_bytes = stream.read(UNCOMPRESSED_SCEP256K1_PUBLIC_KEY_LEN)
        return Identity(public_key_bytes)
    else:
        raise RuntimeError('Unsupported identity type')


def encode(stream: IO[bytes], value: Identity):
    stream.write(bytes([UNCOMPRESSED_SCEP256K1_PUBLIC_KEY]))
    stream.write(value.public_key_bytes)
