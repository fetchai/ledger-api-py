# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

import base64
import json
import random
from hashlib import pbkdf2_hmac

import ecdsa
from Crypto.Cipher import AES

from .identity import Identity


class Entity(Identity):
    """
    An entity is a full private/public key pair.
    """
    @classmethod
    def prompt_load(cls, fp):
        password = input("Please enter password")
        return cls.load(fp, password)

    @classmethod
    def loads(cls, s, password):
        return cls._from_json_object(json.loads(s), password)

    @classmethod
    def load(cls, fp, password):
        return cls._from_json_object(json.load(fp), password)

    @staticmethod
    def from_hex(private_key_hex: str):
        return Entity(bytes.fromhex(private_key_hex))

    @classmethod
    def from_base64(cls, private_key_base64: str):
        return Entity(base64.b64decode(private_key_base64))

    def __init__(self, private_key_bytes=None):

        # construct or generate the private key if one is not specified
        if private_key_bytes is None:
            self._signing_key = ecdsa.SigningKey.generate(curve=self.curve, hashfunc=self.hash_function)
        elif isinstance(private_key_bytes, bytes):
            self._signing_key = ecdsa.SigningKey.from_string(private_key_bytes, curve=self.curve,
                                                             hashfunc=self.hash_function)
        else:
            raise RuntimeError('Unable to load private key from input')

        # cache the binary representations of the private key
        self._private_key_bytes = self._signing_key.to_string()
        self._private_key = base64.b64encode(self._private_key_bytes).decode()

        # construct the base class
        super().__init__(self._signing_key.get_verifying_key())

    @property
    def private_key(self):
        return self._private_key

    @property
    def private_key_hex(self):
        return self.private_key_bytes.hex()

    @property
    def private_key_bytes(self):
        return self._private_key_bytes

    @property
    def signing_key(self):
        return self._signing_key

    def sign(self, message: bytes):
        return self._signing_key.sign(message)

    def prompt_dump(self, fp):
        password = input("Please enter password")
        return self.dump(fp, password)

    def dumps(self, password):
        return json.dumps(self._to_json_object(password))

    def dump(self, fp, password):
        return json.dump(self._to_json_object(password), fp)

    def _to_json_object(self, password):
        encrypted, key_length, init_vec = _encrypt(password, self.private_key_bytes)
        return {
            'key_length': key_length,
            'init_vector': init_vec,
            'privateKey': base64.b64encode(encrypted).decode()
        }

    @classmethod
    def _from_json_object(cls, obj, password):
        privateKey = _decrypt(password, base64.b64decode(obj['privateKey']), obj['key_length'], obj['init_vector'])

        return cls.from_base64(base64.b64encode(privateKey).decode())


def _encrypt(password, data):
    # Hash password to 32 bytes
    hashed_pass = pbkdf2_hmac('sha256', password.encode('ascii'), b'fetchai_private_key_salt', 1000000)

    # Random initialisation vector
    iv = ''.join([chr(random.randint(33, 127)) for i in range(16)])

    aes = AES.new(hashed_pass, AES.MODE_CBC, iv.encode('ascii'))

    # Pad data to multiple of 16
    n = len(data)
    if n % 16 != 0:
        data += ' ' * (16 - n % 16)

    encrypted = aes.encrypt(data)

    return encrypted, n, iv


def _decrypt(password, data, n, iv):
    # Hash password
    hashed_pass = pbkdf2_hmac('sha256', password.encode('ascii'), b'fetchai_private_key_salt', 1000000)

    aes = AES.new(hashed_pass, AES.MODE_CBC, iv.encode('ascii'))

    # Decrypt data, noting original length
    decrypted_data = aes.decrypt(data)[:n]

    # Return original data
    return decrypted_data
