from typing import IO

from fetchai.ledger import crypto


def decode(stream: IO[bytes]) -> crypto.Address:
    raw_address = stream.read(crypto.Address.BYTE_LENGTH)
    return crypto.Address(raw_address)


def encode(stream: IO[bytes], address: crypto.Address):
    stream.write(bytes(address))
