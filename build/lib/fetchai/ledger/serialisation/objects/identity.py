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

import binascii

from fetchai.ledger.crypto import Signing
from fetchai.ledger.serialisation import Serialise, ByteArray


class Identity(Serialise):
    def __init__(self, data=None, params=Signing.curve.openssl_name.encode()):
        self.data = data
        self.params = params

    def __str__(self):
        return "{}: {}".format(binascii.hexlify(self.data), self.params)

    def __eq__(self, other):
        return self.data == other.data and self.params == other.params

    def __hash__(self):
        return hash((self.data, self.params))

    def serialise(self, to_buffer):
        ByteArray(self.data).serialise(to_buffer)
        ByteArray(self.params).serialise(to_buffer)

    def deserialise(self, from_buffer):
        self.data = ByteArray().deserialise(from_buffer).data
        self.params = ByteArray().deserialise(from_buffer).data
