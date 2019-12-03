import io

from fetchai.ledger import crypto


def decode(stream: io.BytesIO) -> crypto.Address:
    raw_address = stream.read(crypto.Address.BYTE_LENGTH)
    return crypto.Address(raw_address)


def encode(stream: io.BytesIO, address: crypto.Address):
    stream.write(bytes(address))
