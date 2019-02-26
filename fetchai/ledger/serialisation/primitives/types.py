#
# ------------------------------------------------------------------------------
#
#   Copyright 2018 Fetch.AI Limited
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

from fetch.ledger.serialisation.stream import pack, unpack
from fetch.ledger.serialisation.interfaces import DataWrapper, NativeDataWrapperInterface, NativeDataWrapper, Serialise

from struct import calcsize


class PrimitiveValue(Serialise, NativeDataWrapper):
    def __init__(self, pack_format, data=None):
        self._pack_format = pack_format
        self._data = data
        # self._size_in_bytes = calcsize(self._pack_format)

    def __eq__(self, other):
        return self.pack_format == other.pack_format and self.data == other.data

    def __hash__(self):
        return hash((self.pack_format, self.data))

    def serialise(self, to_buffer):
        if self._data is None:
            return

        pack(self._pack_format, to_buffer, self.data)

    def deserialise(self, from_buffer):
        self._data, = unpack(self._pack_format, from_buffer)
        return self

    @property
    def data(self):
        return self._data

    @property
    def size_in_bytes(self):
        # return self._size_in_bytes
        return calcsize(self.pack_format)

    @property
    def pack_format(self):
        return self._pack_format


class Char(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="c", data=data)


class SignedChar(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="b", data=data)


class UnsignedChar(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="B", data=data)


class Bool(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="?", data=data)


class SignedShort(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="h", data=data)


class UnsignedShort(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="H", data=data)


class SignedInt(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="i", data=data)


class UnsignedInt(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="I", data=data)


class SignedLong(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="l", data=data)


class UnsignedLong(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="L", data=data)


class SignedLongLong(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="q", data=data)


class UnsignedLongLong(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="Q", data=data)


class SignedSize_t(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="n", data=data)


class Size_t(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="N", data=data)


class Float16b(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="e", data=data)


class Float32b(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="f", data=data)


class Float64b(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="d", data=data)


class NativePointer(PrimitiveValue):
    def __init__(self, data=None):
        PrimitiveValue.__init__(self, pack_format="P", data=data)
