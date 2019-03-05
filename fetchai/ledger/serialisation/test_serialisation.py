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
from fetchai.ledger.serialisation import *

import unittest
import io


class PackingToStreamTest(unittest.TestCase):

    def setUp(self):
        self.bytes = b'\x00\x35\xa0\x00\xf1'

    def test_basic_pack_upack_single_primitive_type(self):
        expected_num = 4.56789
        fmt = "d"
        num_des = None

        stream = io.BytesIO()
        with stream:
            stream.seek(0)
            pack(fmt, stream, expected_num)
            stream.seek(0)
            (num_des,) = unpack(fmt, stream)

        assert expected_num == num_des

    def test_basic_pack_upack_sequence_of_primitive_type(self):
        expected_nums = (4.56789, 0.1234, 3.14)
        fmt = "{}d".format(len(expected_nums))
        stream = io.BytesIO()
        nums_des = None

        with stream:
            stream.seek(0)
            pack(fmt, stream, *expected_nums)
            stream.seek(0)
            nums_des = unpack(fmt, stream)

        assert expected_nums == nums_des


class NativeDynamicArrayTest(unittest.TestCase):

    def setUp(self):
        self.bytes = b'\x00\x35\xa0\x00\xf1'

    def test_bytes_as_input_data(self):
        a = NativeDynamicArray(item_pack_format="s", data=self.bytes)
        a_des = NativeDynamicArray(item_pack_format="s")

        stream = io.BytesIO()
        with stream:
            a.serialise(stream)
            stream.seek(0)
            a_des.deserialise(stream)

        assert self.bytes == a_des.data

    def test_collection_of_primitive_type_as_input_data(self):
        item_pack_format = "d"
        expected_list = [1.234, 0.459035, 1.864, 4.7021]

        a = NativeDynamicArray(item_pack_format=item_pack_format, data=expected_list)
        a_des = NativeDynamicArray(item_pack_format=item_pack_format)

        stream = io.BytesIO()
        with stream:
            a.serialise(stream)
            stream.seek(0)
            a_des.deserialise(stream)

        assert expected_list == list(a_des.data), "expected_list={}, received data={}".format(expected_list,
                                                                                              list(a_des.data))


class ListTest(unittest.TestCase):

    def _test_list(self, type_of_value, input_list, expected_list=None):
        if expected_list is None:
            expected_list = input_list

        a = List(type_of_value=type_of_value, collection=input_list)
        a_des = List(type_of_value=type_of_value)

        stream = io.BytesIO()
        with stream:
            a.serialise(stream)
            stream.seek(0)
            a_des.deserialise(stream)

        assert expected_list == list(a_des.data), "expected_list={}, received data={}".format(expected_list,
                                                                                              list(a_des.data))

    def test_primitive_char_as_input_data(self):
        self._test_list(type_of_value=Char, input_list=[b'a', b's', b'g', b'd', b'f', b'g'])

    def test_bytes_as_input_data(self):
        self._test_list(type_of_value=ByteArray, input_list=[b'asdfdasfg', b'bcvn347456', b',.[p43-0.,]', b'3,.43'])

    def test_bytes_primitives_mixed_with_byte_array_as_input_data(self):
        list_of_prims = [b'asdfdasfg', b'bcvn347456', b',.[p43-0.,]', b'3,.43']
        list_of_prims_for_byte_array = [b'$!@#,.mhg', b'inm.dp92#%$^@']
        list_of_byte_arrays = [ByteArray(val) for val in list_of_prims_for_byte_array]

        expected_list = list_of_prims + list_of_prims_for_byte_array
        input_list = list_of_prims + list_of_byte_arrays
        self._test_list(
            type_of_value=ByteArray,
            input_list=input_list,
            expected_list=expected_list)


class DictTest(unittest.TestCase):

    def _test_dict(self, type_of_key, type_of_value, input_dict, expected_dict=None):
        if expected_dict is None:
            expected_dict = input_dict

        a = Dict(type_of_key=type_of_key, type_of_value=type_of_value, collection=input_dict)
        a_des = Dict(type_of_key=type_of_key, type_of_value=type_of_value)

        stream = io.BytesIO()
        with stream:
            a.serialise(stream)
            stream.seek(0)
            a_des.deserialise(stream)

        assert expected_dict == a_des.data, "expected_set={}, received data={}".format(expected_dict, a_des.data)

    def test_primitive_type_as_input_data(self):
        self._test_dict(type_of_key=ByteArray, type_of_value=ByteArray,
                        input_dict={b'a': b'dfsda', b's': b'54624', b'g': b'sadfas', b'd': b'dasfS', b'f': b'354^',
                                    b'g': b'@#'})

    def test_primitive_type_as_input_data_2(self):
        self._test_dict(type_of_key=UnsignedInt, type_of_value=ByteArray,
                        input_dict={1: b'dfsda', 2: b'54624', 3: b'sadfas', 4: b'dasfS', 5: b'354^', 6: b'@#'})

    def test_primitive_type_as_input_data_3(self):
        self._test_dict(type_of_key=UnsignedInt, type_of_value=Float64b,
                        input_dict={1: 7.123, 2: 0.345, 3: 5.14, 4: 3.45, 5: 6, 6: 9.56})

    def test_bytes_primitives_mixed_with_byte_array_as_input_data(self):
        input_dict = {
            ByteArray(b'a'): b'dfsda',
            b's': b'54624',
            ByteArray(b'g'): ByteArray(b'sadfas'),
            b'd': ByteArray(b'dasfS'),
            b'f': b'354^',
            b'g': b'@#'
        }

        expected_dict = {}
        for key, val in input_dict.items():
            if isinstance(key, DataWrapper):
                key = key.data
            if isinstance(val, DataWrapper):
                val = val.data
            expected_dict[key] = val

        self._test_dict(type_of_key=ByteArray, type_of_value=ByteArray, input_dict=input_dict,
                        expected_dict=expected_dict)


class SetTest(unittest.TestCase):

    def _test_set(self, type_of_value, input_set, expected_set=None):
        if expected_set is None:
            expected_set = input_set

        a = Set(type_of_value=type_of_value, collection=input_set)
        a_des = Set(type_of_value=type_of_value)

        stream = io.BytesIO()
        with stream:
            a.serialise(stream)
            stream.seek(0)
            a_des.deserialise(stream)

        assert expected_set == a_des.data, "expected_set={}, received data={}".format(expected_set, a_des.data)

    def test_primitive_type_as_input_data(self):
        self._test_set(type_of_value=ByteArray, input_set=set([b'a', b's', b'g', b'd', b'f', b'g']))

    def test_primitive_type_as_input_data_2(self):
        self._test_set(type_of_value=UnsignedInt, input_set=set([0, 1, 2, 3, 4, 5]))

    def test_primitive_type_as_input_data_3(self):
        self._test_set(type_of_value=Float64b, input_set=set([7.123, 0.345, 5.14, 3.45, 6, 9.56]))

    def test_bytes_primitives_mixed_with_byte_array_as_input_data(self):
        input_set = set([
            ByteArray(b'a'),
            b's',
            ByteArray(b'g'),
            b'd',
            ByteArray(b'354^'),
            b'@#'
        ])

        expected_set = set()
        for val in input_set:
            if isinstance(val, DataWrapper):
                val = val.data
            expected_set.add(val)

        self._test_set(type_of_value=ByteArray, input_set=input_set, expected_set=expected_set)
