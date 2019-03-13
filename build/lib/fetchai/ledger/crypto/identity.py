import ecdsa
import hashlib
import base64
import binascii


class Identity:
    def __init__(self, private_key_bytes=None, curve=None, digest=None):
        if curve is None:
            curve = ecdsa.SECP256k1
        if digest is None:
            digest = hashlib.sha256

        # construct or generate the private key
        if private_key_bytes is None:
            self._signing_key = ecdsa.SigningKey.generate(curve=curve, hashfunc=digest)
        else:
            self._signing_key = ecdsa.SigningKey.from_string(private_key_bytes, curve=curve)

        # extract the verifying key from the signing (private) key
        self._verifying_key = self._signing_key.get_verifying_key()

        # extract the bytes for the private and public keys
        self._private_key_bytes = self._signing_key.to_string()
        self._public_key_bytes = self._verifying_key.to_string()

    @property
    def public_key(self):
        return base64.b64encode(self.public_key_bytes).decode()

    @property
    def public_key_hex(self):
        return binascii.hexlify(self.public_key_bytes).decode()

    @property
    def public_key_bytes(self):
        return self._public_key_bytes

    @property
    def private_key(self):
        return base64.b64encode(self.private_key_bytes).decode()

    @property
    def private_key_hex(self):
        return binascii.hexlify(self.private_key_bytes).decode()

    @property
    def private_key_bytes(self):
        return self._private_key_bytes
