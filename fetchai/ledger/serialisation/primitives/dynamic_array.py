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

from fetchai.ledger.serialisation.primitives.types import *
from fetchai.ledger.serialisation.primitives.static_array import NativeStaticArray

from struct import calcsize


class NativeDynamicArray(Serialise, NativeDataWrapperInterface):
    _size_format = "Q"

    def __init__(self, item_pack_format, data=None):
        self._native_static_array = NativeStaticArray(item_pack_format=item_pack_format, data=data)

    def __eq__(self, other):
        return self._native_static_array == other._native_static_array

    def __hash__(self):
        return self._native_static_array.__hash__()

    @property
    def item_pack_format(self):
        return self._native_static_array.item_pack_format

    @property
    def pack_format(self):
        array_format = "{}{{}}{}".format(self._size_format, self._native_static_array.pack_format)
        return array_format.format(len(self.data))

    @property
    def data(self):
        return self._native_static_array.data

    @property
    def size_in_bytes(self):
        return calcsize(self.pack_format)

    def serialise(self, to_buffer):
        if self.data is None:
            return

        pack(self._size_format, to_buffer, len(self.data))
        self._native_static_array.serialise(to_buffer)

    def deserialise(self, from_buffer):
        num_of_elements, = unpack(self._size_format, from_buffer)
        self._native_static_array = NativeStaticArray(item_pack_format=self._native_static_array.item_pack_format,
                                                      data=range(num_of_elements))
        self._native_static_array.deserialise(from_buffer)
        return self


class CharNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="c")


class SignedCharNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="b")


class UnsignedCharNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="B")


class BoolNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="?")


class SignedShortNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="h")


class UnsignedShortNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="H")


class SignedIntNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="i")


class UnsignedIntNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="I")


class SignedLongNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="l")


class UnsignedLongNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="L")


class SignedLongLongNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="q")


class UnsignedLongLongNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="Q")


class SignedSize_tNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="n")


class Size_tNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="N")


class Float16bNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="e")


class Float32bNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="f")


class Float64bNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="d")


class PointerNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="P")


class StringNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="s")


class ByteArray(StringNativeDynamicArray):
    pass


class PascalStringNativeDynamicArray(NativeDynamicArray):
    def __init__(self, data=None):
        NativeDynamicArray.__init__(self, data=data, item_pack_format="p")
