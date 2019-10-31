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
import hashlib
import json
import logging
import random
import re
import bcrypt
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

        while not _strong_password(password):
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
        encrypted, key_length, init_vec, salt = _encrypt(password, self.private_key_bytes)
        return {
            'key_length': key_length,
            'init_vector': init_vec,
            'password_salt': salt,
            'privateKey': base64.b64encode(encrypted).decode()
        }

    @classmethod
    def _from_json_object(cls, obj, password):
        private_key = _decrypt(password,
                               obj['password_salt'],
                               base64.b64decode(obj['privateKey']),
                               obj['key_length'],
                               obj['init_vector'])

        return cls.from_base64(base64.b64encode(private_key).decode())


def _encrypt(password: str, data: bytes):
    """
    Encryption schema for private keys
    :param password: plaintext password to use for encryption
    :param data: plaintext data to encrypt
    :return: encrypted data, length of original data, initialisation vector for aes, password hashing salt
    """
    # Generate hash from password
    salt = bcrypt.gensalt(rounds=14)
    hashed_pass = bcrypt.hashpw(password.encode(), salt)

    # SHA256 to 32 bytes
    sha256 = hashlib.sha256()
    sha256.update(hashed_pass)
    hashed_pass = sha256.digest()

    # Random initialisation vector
    iv = ''.join([chr(random.randint(33, 127)) for _ in range(16)])

    # Encrypt data using AES
    aes = AES.new(hashed_pass, AES.MODE_CBC, iv.encode('ascii'))

    # Pad data to multiple of 16
    n = len(data)
    if n % 16 != 0:
        data += ' ' * (16 - n % 16)

    encrypted = aes.encrypt(data)

    return encrypted, n, iv, salt.decode()


def _decrypt(password: str, salt: str, data: bytes, n: int, iv: str):
    """
    Decryption schema for private keys
    :param password: plaintext password used for encryption
    :param salt: password hashing salt
    :param data: encrypted data string
    :param n: length of original plaintext data
    :param iv: initialisation vector for aes
    :return: decrypted data as plaintext
    """
    # Hash password
    hashed_pass = bcrypt.hashpw(password.encode(), salt.encode())

    sha256 = hashlib.sha256()
    sha256.update(hashed_pass)
    hashed_pass = sha256.digest()

    # Decrypt data, noting original length
    aes = AES.new(hashed_pass, AES.MODE_CBC, iv.encode('ascii'))
    decrypted_data = aes.decrypt(data)[:n]

    # Return original data
    return decrypted_data


def _strong_password(password: str):
    """
    Checks that a password is of sufficient length and contains all character classes
    :param password:
    :return: True if password is strong
    """
    if len(password) < 14:
        logging.warning("Please enter a password at least 14 characters long")
        return False

    if not re.search(r'[a-z]+', password):
        logging.warning("Password must contain at least one lower case character")
        return False

    if not re.search(r'[A-Z]+', password):
        logging.warning("Password must contain at least one upper case character")
        return False

    if not re.search(r'[0-9]+', password):
        logging.warning("Password must contain at least one number")
        return False

    if not re.search(r'[#?!@$%^&*\-+=/\':;,.()\[\]{}~`_\\]', password):
        logging.warning("Password must contain at least one symbol")
        return False

    return True
