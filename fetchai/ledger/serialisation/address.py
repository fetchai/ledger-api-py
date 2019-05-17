import io

from fetchai.ledger.crypto import Address


def decode(stream: io.BytesIO) -> Address:
    raw_address = stream.read(Address.BYTE_LENGTH)
    return Address(raw_address)


def encode(stream: io.BytesIO, address: Address):
    stream.write(bytes(address))
