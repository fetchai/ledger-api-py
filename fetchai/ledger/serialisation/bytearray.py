from typing import IO

from . import integer


def decode(stream: IO[bytes]) -> bytes:
    length = integer.decode(stream)
    return stream.read(length)


def encode(stream: IO[bytes], value: bytes):
    integer.encode(stream, len(value))
    stream.write(value)
