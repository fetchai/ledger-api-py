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


from fetch.ledger.serialisation.primitives.types import *
from fetch.ledger.serialisation.interfaces import NativeDataWrapperInterface, Serialise

from struct import calcsize


class NativeStaticArray(Serialise, NativeDataWrapperInterface):
    def __init__(self, item_pack_format, data=None):
        self._item_pack_format = item_pack_format
        self._array_format = "{{}}{}".format(item_pack_format)
        self._data = data

    def __eq__(self, other):
        return self._item_pack_format == other._item_pack_format and self._data == other._data

    def __hash__(self):
        if isinstance(self._data, bytes) or isinstance(self._data, str):
            tpl = self._item_pack_format, self._data
        else:
            tpl = (self._item_pack_format,) + self._data

        return hash(tpl)

    @property
    def item_pack_format(self):
        return self._item_pack_format

    @property
    def pack_format(self):
        return self._array_format.format(len(self._data))

    @property
    def data(self):
        return self._data

    @property
    def size_in_bytes(self):
        return calcsize(self.pack_format)

    def serialise(self, to_buffer):
        if self._data is None:
            return

        pf = self.pack_format
        if self._item_pack_format == "s" or self._item_pack_format == "p":
            pack(pf, to_buffer, self._data)
        else:
            pack(pf, to_buffer, *self._data)

    def deserialise(self, from_buffer):

        data_tuple = unpack(self.pack_format, from_buffer)

        if self._item_pack_format == "s" or self._item_pack_format == "p":
            self._data, = data_tuple
        else:
            self._data = data_tuple

        return self


class CharNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="c")


class SignedCharNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="b")


class UnsignedCharNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="B")


class BoolNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="?")


class SignedShortNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="h")


class UnsignedShortNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="H")


class SignedIntNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="i")


class UnsignedIntNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="I")


class SignedLongNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="l")


class UnsignedLongNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="L")


class SignedLongLongNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="q")


class UnsignedLongLongNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="Q")


class SignedSize_tNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="n")


class Size_tNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="N")


class Float16bNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="e")


class Float32bNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="f")


class Float64bNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="d")


class PointerNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="P")


class StringNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="s")


class PascalStringNativeStaticArray(NativeStaticArray):
    def __init__(self, data=None):
        NativeStaticArray.__init__(self, data=data, item_pack_format="p")
