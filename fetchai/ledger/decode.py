import base64
from typing import Union


def decode_hex_or_b64(encoded: Union[str, bytes]) -> bytes:
    """Decode an input encoded as hex or base64 as bytes.

    :type encoded: str or bytes
    """

    hex_prefix = '0x'
    b64_padding = '='

    if isinstance(encoded, str):
        encoded_str = encoded
    elif isinstance(encoded, bytes):
        encoded_str = encoded.decode()
    else:
        raise TypeError('Expected argument to be bytes or str')

    try:
        if encoded_str.startswith(hex_prefix) and not encoded_str.endswith(b64_padding) and len(encoded_str) > 2:
            return bytes.fromhex(encoded_str[2:])
        else:
            return bytes.fromhex(encoded_str)
    except ValueError:
        # hex decoding did not work - attempt base64
        padding = b64_padding * (len(encoded_str) % 4)

        return base64.b64decode(encoded_str + padding)
