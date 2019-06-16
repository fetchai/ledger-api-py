import io

from . import integer


def decode(stream: io.BytesIO) -> bytes:
    length = integer.decode(stream)
    return stream.read(length)


def encode(stream: io.BytesIO, value: bytes):
    integer.encode(stream, len(value))
    stream.write(value)
