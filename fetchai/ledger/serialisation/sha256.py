import hashlib
from typing import Union


def sha256_hash(data: Union[str, bytes]) -> bytes:
    """
    Calculates the sha256 hash of a string

    :param data: byte or character string
    :return: byte string
    """
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.digest()


def sha256_hex(data: Union[str, bytes]) -> str:
    """
    Calculates sha256 hash of a string, then encodes it to a hex string

    :param data: byte or character string
    :return: hex encoded character string
    """
    return sha256_hash(data).hex()
