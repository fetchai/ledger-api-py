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
import getpass
import json
import logging
import os
import re
from hashlib import pbkdf2_hmac
from typing import Tuple, IO

import ecdsa
import pyaes

from .identity import Identity

WEAK_PASSWORD_TEXT = "Insufficiently strong password: password must contain 14 chars or more, with one or more uppercase, lowercase, numeric and special character"


class Entity(Identity):

    @staticmethod
    def is_strong_password(password: str) -> bool:
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
    def private_key(self) -> str:
        return self._private_key

    @property
    def private_key_hex(self) -> str:
        return self.private_key_bytes.hex()

    @property
    def private_key_bytes(self) -> bytes:
        return self._private_key_bytes

    @property
    def signing_key(self):
        return self._signing_key

    def sign(self, message: bytes) -> bytes:
        return self._signing_key.sign(message)

    @classmethod
    def loads(cls, s: str, password: str) -> 'Entity':
        return cls._from_json_object(json.loads(s), password)

    @classmethod
    def load(cls, fp: IO[str], password) -> 'Entity':
        return cls._from_json_object(json.load(fp), password)

    @classmethod
    def prompt_load(cls, fp: IO[str]) -> 'Entity':
        password = getpass.getpass('Please enter password: ', stream=None)
        return cls.load(fp, password)

    def prompt_dump(self, fp: IO[str]):

        # request a strong password from the use
        password = getpass.getpass('Please enter password.........: ', stream=None)
        while not self.is_strong_password(password):
            password = getpass.getpass('Weak password please try again: ', stream=None)

        # request a confirmation from the user
        while True:
            confirmation = getpass.getpass('Please confirm password.......: ', stream=None)
            if password == confirmation:
                break
            print('Password does not match please try again')

        return self.dump(fp, password)

    def dumps(self, password: str) -> str:
        if not self.is_strong_password(password):
            raise RuntimeError(WEAK_PASSWORD_TEXT)
        return json.dumps(self._to_json_object(password))

    def dump(self, fp: IO[str], password: str):
        if not self.is_strong_password(password):
            raise RuntimeError(WEAK_PASSWORD_TEXT)
        return json.dump(self._to_json_object(password), fp)

    def _to_json_object(self, password: str):
        encrypted, key_length, init_vec, salt = _encrypt(password, self.private_key_bytes)
        return {
            'key_length': key_length,
            'init_vector': base64.b64encode(init_vec).decode(),
            'password_salt': base64.b64encode(salt).decode(),
            'privateKey': base64.b64encode(encrypted).decode()
        }

    @classmethod
    def _from_json_object(cls, obj, password: str):
        private_key = _decrypt(password,
                               base64.b64decode(obj['password_salt']),
                               base64.b64decode(obj['privateKey']),
                               obj['key_length'],
                               base64.b64decode(obj['init_vector']))

        return cls.from_base64(base64.b64encode(private_key).decode())


def _encrypt(password: str, data: bytes) -> Tuple[bytes, int, bytes, bytes]:
    """
    Encryption schema for private keys
    :param password: plaintext password to use for encryption
    :param data: plaintext data to encrypt
    :return: encrypted data, length of original data, initialisation vector for aes, password hashing salt
    """
    # Generate hash from password
    salt = os.urandom(16)
    hashed_pass = pbkdf2_hmac('sha256', password.encode(), salt, 2000000)

    # Random initialisation vector
    iv = os.urandom(16)

    # Encrypt data using AES
    aes = pyaes.AESModeOfOperationCBC(hashed_pass, iv=iv)

    # Pad data to multiple of 16
    n = len(data)
    if n % 16 != 0:
        data += b' ' * (16 - n % 16)

    encrypted = b''
    while len(data):
        encrypted += aes.encrypt(data[:16])
        data = data[16:]

    return encrypted, n, iv, salt


def _decrypt(password: str, salt: bytes, data: bytes, n: int, iv: bytes) -> bytes:
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
    hashed_pass = pbkdf2_hmac('sha256', password.encode(), salt, 2000000)

    # Decrypt data, noting original length
    aes = pyaes.AESModeOfOperationCBC(hashed_pass, iv=iv)

    decrypted = b''
    while len(data):
        decrypted += aes.decrypt(data[:16])
        data = data[16:]
    decrypted_data = decrypted[:n]

    # Return original data
    return decrypted_data
