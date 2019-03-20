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
import binascii
import io
import json

import ecdsa

from fetchai.ledger.crypto import Signing
from fetchai.ledger.serialisation import Serialise, ByteArray, UnsignedLongLong, Dict, List, Set
from fetchai.ledger.serialisation.objects.identity import Identity
from fetchai.ledger.serialisation.objects.signature import Signature


class Signatories(Dict):
    def __init__(self, signatories_dictionary=None):
        Dict.__init__(self, type_of_key=Identity, type_of_value=Signature, collection=signatories_dictionary)


class TxBase(Serialise):
    def __init__(self, contract_name=None, fee=None, resources=None, data=None):
        self._signing_io_stream = io.BytesIO()
        self._base_data_size = None
        self._base_hasher = None

        self.contract_name = contract_name
        self.fee = fee
        self.resources = resources
        self.data = data

    def __str__(self, ):
        return 'contract name: "{}",\nfee: {},\nresources: {},\ncontract data: {}'.format(self._contract_name,
                                                                                          self._fee,
                                                                                          [binascii.hexlify(res) for res
                                                                                           in self._resources],
                                                                                          self._data)

    def __eq__(self, other):
        return self._contract_name == other._contract_name and \
               self._fee == other._fee and \
               self._resources == other._resources and \
               self._data == other._data

    def __hash__(self):
        data_to_hash = (self._contract_name, self._fee, self._data)
        if self._resources is not None:
            data_to_hash += tuple(sorted(self._resources))
        return hash(data_to_hash)

    def _invalidate(self):
        self._base_data_size = None

    @property
    def _is_invalidated(self):
        return self._base_data_size is None or self._base_data_size == 0

    @property
    def contract_name(self):
        return self._contract_name

    @contract_name.setter
    def contract_name(self, value):
        self._contract_name = value
        self._invalidate()

    @property
    def fee(self):
        return self._fee

    @fee.setter
    def fee(self, value):
        self._fee = value
        self._invalidate()

    @property
    def resources(self):
        return self._resources

    @resources.setter
    def resources(self, value):
        self._resources = value
        self._invalidate()

    @property
    def data(self):
        return self._data

    def serialised_tx_base_data(self):
        return self._signing_io_stream.getvalue()[:self._base_data_size]

    @data.setter
    def data(self, value):
        self._data = value
        self._invalidate()

    def update(self):
        if not self._is_invalidated:
            return

        self._signing_io_stream.seek(0)
        TxBase.serialise(self, self._signing_io_stream)

        self._base_data_size = self._signing_io_stream.tell()
        self._base_hasher = Signing.digest()
        self._base_hasher.update(TxBase.serialised_tx_base_data(self))

    def digest_for_signing(self, public_key_data):
        self.update()
        identity = Identity(data=public_key_data)
        stream = io.BytesIO()
        identity.serialise(stream)
        data = stream.getvalue()
        resulting_hasher = self._base_hasher.copy()
        resulting_hasher.update(data)
        # self._print_sign_data("", resulting_hasher.digest(), data)
        return resulting_hasher.digest(), identity

    def serialise(self, to_buffer):
        if self._is_invalidated:
            ByteArray(self._contract_name).serialise(to_buffer)
            UnsignedLongLong(self._fee).serialise(to_buffer)
            List(type_of_value=ByteArray, collection=sorted(self._resources) if self._resources else []).serialise(
                to_buffer)
            ByteArray(self._data).serialise(to_buffer)
        else:
            to_buffer.write(TxBase.serialised_tx_base_data(self))

    def deserialise(self, from_buffer):
        self.contract_name = ByteArray().deserialise(from_buffer).data
        self.fee = UnsignedLongLong().deserialise(from_buffer).data
        self.resources = Set(type_of_value=ByteArray).deserialise(from_buffer).data
        self.data = ByteArray().deserialise(from_buffer).data
        # self.update()

    def _print_sign_data(self, prefix, digest, identity_serialised_data):
        print('{}: digest[hex]={},\ntx_ser_data[hex]={}.\nidentity_ser_data[hex]={}\n'.format(prefix,
                                                                                              binascii.hexlify(digest),
                                                                                              binascii.hexlify(
                                                                                                  self._signing_io_stream.getvalue()),
                                                                                              binascii.hexlify(
                                                                                                  identity_serialised_data)))
        stream = io.BytesIO()
        stream.write(self._signing_io_stream.getvalue())
        stream.write(identity_serialised_data)
        hash = Signing.digest()
        hash.update(stream.getvalue())
        print('{}: digest[hex]={},\nhashed_data[hex]={}'.format(prefix, binascii.hexlify(hash.digest()),
                                                                binascii.hexlify(stream.getvalue())))

    def sign(self, private_key):
        if isinstance(private_key, ecdsa.SigningKey):
            priv_key = private_key
        elif isinstance(private_key, bytes):
            priv_key = Signing.create_private_key(private_key)
        else:
            raise TypeError("Input private key is neither `ecdsa.SigningKey` type nor `bytes` type.")

        digest, identity = self.digest_for_signing(priv_key.get_verifying_key().to_string())

        signature_data = priv_key.sign_digest(digest)
        signature = Signature(data=signature_data)
        return identity, signature

    def verify(self, signature_data, public_key):
        if isinstance(public_key, ecdsa.VerifyingKey):
            pub_key = public_key
        elif isinstance(public_key, bytes):
            pub_key = Signing.create_public_key(public_key)
        else:
            raise TypeError("Input public key is neither `ecdsa.VerifyingKey` type nor `bytes` type.")

        digest, _ = self.digest_for_signing(pub_key.to_string())

        try:
            pub_key.verify_digest(signature_data, digest)
            return True
        except ecdsa.keys.BadSignatureError:
            pass

        return False

    def get_metadata(self):
        metadata = {"contract_name": self._contract_name.decode(), "fee": self._fee,
                    "resources": [base64.b64encode(res).decode() for res in self._resources],
                    "data": base64.b64encode(self._data).decode()}
        return metadata


class Tx(TxBase):
    def __init__(self, contract_name=None, fee=None, resources=None, data=None, signatories=None):
        TxBase.__init__(self, contract_name=contract_name, fee=fee, resources=resources, data=data)
        self._signatories = None

    def __str__(self):
        return '{},\nsignatories: {}'.format(TxBase.__str__(self),
                                             [(str(iden), str(sig)) for iden, sig, in self._signatories.items()])

    def __eq__(self, other):
        return TxBase.__eq__(self, other) and self._signatories == other._signatories

    def __hash__(self):
        _hash = TxBase.__hash__(self)
        if self._signatories is not None:
            _hash ^= hash(tuple(sorted(self._signatories.items())))
        return _hash

    @property
    def signatories(self):
        return self._signatories

    @signatories.setter
    def signatories(self, value):
        self._signatories = value

    def sign(self, private_key):
        identity, signature = TxBase.sign(self, private_key)
        if self._signatories is None:
            self._signatories = {}
        self._signatories[identity] = signature

    # TODO(private issue 13): This doesn't match the base classs
    def verify(self):
        for identity, signature in self._signatories.items():
            if not TxBase.verify(self, signature.data, identity.data):
                return False

        return len(self._signatories) > 0

    def serialise(self, to_buffer):
        TxBase.serialise(self, to_buffer)
        Signatories(signatories_dictionary=self._signatories if self._signatories else {}).serialise(to_buffer)

    def deserialise(self, from_buffer):
        TxBase.deserialise(self, from_buffer)
        self._signatories = Signatories().deserialise(from_buffer).data
        return self

    def get_metadata(self):
        metadata = TxBase.get_metadata(self)
        signatories = {}

        stream = io.BytesIO()
        with stream:
            for identity, signature in self._signatories.items():
                stream.seek(0)
                identity.serialise(stream)
                identity_data = stream.getvalue()[:stream.tell()]
                identity_b64 = base64.b64encode(identity_data).decode()

                stream.seek(0)
                signature.serialise(stream)
                signature_data = stream.getvalue()[:stream.tell()]
                signature_b64 = base64.b64encode(signature_data).decode()

                signatories[identity_b64] = signature_b64

        metadata["signatories"] = signatories

        return metadata

    def to_wire_format(self, include_metadata=False):
        wire_format = {"ver": "1.0"}
        if include_metadata:
            wire_format["metadata"] = self.get_metadata()

        stream = io.BytesIO()
        self.serialise(stream)
        tx_data = stream.getvalue()[:stream.tell()]
        tx_data_b64 = base64.b64encode(tx_data).decode()
        wire_format["data"] = tx_data_b64

        return json.dumps(wire_format)

    @classmethod
    def from_wire_format(cls, tx_wire_format_data):
        wire_format = json.loads(tx_wire_format_data)
        tx_data_b64 = wire_format["data"]
        tx_data = base64.b64decode(tx_data_b64)
        stream = io.BytesIO(tx_data)
        stream.seek(0)
        return Tx().deserialise(stream)
