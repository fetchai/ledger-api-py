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
from .stream import pack, unpack
from .interfaces import DataWrapper, NativeDataWrapper, Serialise
from .primitives.dynamic_array import NativeDynamicArray


class Params(Serialise):
    def __init__(self, *args):
        self._args = args

    def __eq__(self, other):
        return self._args == other._args

    def __hash__(self):
        return hash(self._args)

    @property
    def data(self):
        return self._args

    def serialise(self, to_buffer):
        if self._args:
            for arg in self._args:
                Serialise.check_is_serialisable(arg)
                arg.serialise(to_buffer)

    def deserialise(self, from_buffer):
        if self._args:
            for arg in self._args:
                Serialise.check_is_serialisable(arg)
                arg.deserialise(from_buffer)


class List(Serialise):
    size_format = "Q"

    def __init__(self, type_of_value, collection=None):
        self._is_native_type = issubclass(type_of_value, NativeDataWrapper)
        self._is_data_wrapper = issubclass(type_of_value, DataWrapper)

        if type_of_value:
            if not issubclass(type_of_value, Serialise):
                raise TypeError("Input value `type_of_value` must be be derived from of `Serialise` type")
            self._type_of_value = type_of_value

            if self._is_native_type:
                self._sample_element = type_of_value()

        if collection is not None:
            if not isinstance(collection, list):
                raise TypeError("Input collection must be of `list` type")

        self._collection = collection

    def serialise(self, to_buffer):
        if self._is_native_type:
            va = NativeDynamicArray(item_pack_format=self._sample_element.pack_format, data=self._collection)
            va.serialise(to_buffer)
        else:
            pack(self.size_format, to_buffer, len(self._collection))
            for item in self._collection:
                if isinstance(item, bytes):
                    item = self._type_of_value(item)
                item.serialise(to_buffer)

    def deserialise(self, from_buffer):
        if self._is_native_type:
            va = NativeDynamicArray(item_pack_format=self._sample_element.pack_format)
            va.deserialise(from_buffer)
            self._collection = list(va.data)
        else:
            num_of_elements, = unpack(self.size_format, from_buffer)
            self._collection = []
            for _ in range(0, num_of_elements):
                value = self._type_of_value()
                value.deserialise(from_buffer)
                self._collection.append(value.data if self._is_data_wrapper else value)

        return self

    @property
    def data(self):
        return self._collection


class Dict(Serialise):
    size_format = "Q"

    def __init__(self, type_of_value, type_of_key, collection=None):
        self._is_key_native_type = issubclass(type_of_key, NativeDataWrapper)
        self._is_value_native_type = issubclass(type_of_value, NativeDataWrapper)
        self._is_key_data_wrapper = issubclass(type_of_key, DataWrapper)
        self._is_value_data_wrapper = issubclass(type_of_value, DataWrapper)

        if type_of_value:
            if not issubclass(type_of_value, Serialise):
                raise TypeError("Input value `type_of_value` must be be derived from of `Serialise` type")
            self._type_of_value = type_of_value

            if self._is_value_native_type:
                self._value_sample = type_of_value()

        if type_of_key:
            if not issubclass(type_of_key, Serialise):
                raise TypeError("Input value `type_of_key` must be be derived from of `Serialise` type")
            self._type_of_key = type_of_key

            if self._is_key_native_type:
                self._key_sample = type_of_key()

        if collection is not None:
            if not isinstance(collection, dict):
                raise TypeError("Input collection must be of `dict` type")

        self._collection = collection

    def serialise(self, to_buffer):
        pack(self.size_format, to_buffer, len(self._collection))

        for key, value in self._collection.items():
            if self._is_key_native_type or isinstance(key, bytes):
                key = self._type_of_key(key)

            if self._is_value_native_type or isinstance(value, bytes):
                value = self._type_of_value(value)

            key.serialise(to_buffer)
            value.serialise(to_buffer)

    def deserialise(self, from_buffer):
        num_of_elements, = unpack(self.size_format, from_buffer)
        self._collection = {}
        for _ in range(0, num_of_elements):
            key = self._type_of_key()
            value = self._type_of_value()

            key.deserialise(from_buffer)
            value.deserialise(from_buffer)

            if self._is_key_native_type or self._is_key_data_wrapper:
                key = key.data

            if self._is_value_native_type or self._is_value_data_wrapper:
                value = value.data

            self._collection[key] = value

        return self

    @property
    def data(self):
        return self._collection


class Set(Serialise):
    size_format = "Q"

    def __init__(self, type_of_value, collection=None):
        self._is_value_native_type = issubclass(type_of_value, NativeDataWrapper)
        self._is_data_wrapper = issubclass(type_of_value, DataWrapper)

        if type_of_value:
            if not issubclass(type_of_value, Serialise):
                raise TypeError("Input value `type_of_value` must be be derived from of `Serialise` type")
            self._type_of_value = type_of_value

            if self._is_value_native_type:
                self._value_sample = type_of_value()

        if collection is not None:
            if not isinstance(collection, set):
                raise TypeError("Input collection must be of `set` type")

        self._collection = collection

    def serialise(self, to_buffer):
        pack(self.size_format, to_buffer, len(self._collection))

        for value in self._collection:
            if self._is_value_native_type or isinstance(value, bytes):
                value = self._type_of_value(value)

            value.serialise(to_buffer)

    def deserialise(self, from_buffer):
        num_of_elements, = unpack(self.size_format, from_buffer)
        self._collection = set()
        for _ in range(0, num_of_elements):
            value = self._type_of_value()

            value.deserialise(from_buffer)

            if self._is_value_native_type or self._is_data_wrapper:
                value = value.data

            self._collection.add(value)

        return self

    @property
    def data(self):
        return self._collection
