import binascii


class BitVector:

    @staticmethod
    def from_bytes(data: bytes, bit_size: int):
        """
        Takes a sequence of bytes, packs it into a BitVector object and returns the BitVector.

        :param data: a sequence of bytes in bytes object form.
        :param bit_size: an integer representing the BitVector() size.
        :return: the BitVector object containing the buffered data.
        """
        # ensure the bit size matches the expectation
        min_size = max((len(data) - 1) * 8, 1)
        max_size = len(data) * 8
        assert min_size <= bit_size <= max_size

        bits = BitVector()
        bits._size = bit_size
        bits._byte_size = (bit_size + 7) // 8
        bits._buffer = bytearray(reversed(data))

        return bits

    @classmethod
    def from_hex_string(cls, hex_data):
        """
        Takes a hexadecimal string, converts it to a binary sequence, and sends it to the from_bytes() method.

        :param hexdata: a hexadecimal string.
        :return: the BitVector object returned by from_bytes().
        """
        decoded_bytes = binascii.unhexlify(hex_data)
        return cls.from_bytes(decoded_bytes, len(decoded_bytes) * 8)

    def __init__(self, size=None):
        """
        Constructor method that builds a BitVector with a given integer size or as a copy of a given BitVector.

        :param size: an integer, or a BitVector, or None.
        """
        if size is None:
            size = 0

        if isinstance(size, BitVector):
            self._size = size._size
            self._byte_size = size._byte_size
            self._buffer = bytearray(size._buffer)
        else:
            self._size = int(size)
            self._byte_size = (self._size + 7) // 8
            self._buffer = bytearray([0] * self._byte_size)

    def __bytes__(self):
        """
        Converts the bytearray representation of this BitVector to a bytes object.

        :return: a bytes object representation of this BitVector.
        """
        return bytes(reversed(self._buffer))

    def __len__(self):
        """
        Returns the size of the BitVector object.

        :return: integer representation of the size of this BitVector.
        """
        return self._size

    def __eq__(self, other):
        """
        Performs equality check on this BitVector and another BitVector object.

        :param other: another BitVector object.
        :return: true or false.
        """
        if len(self) == len(other):
            return bytes(self) == bytes(other)
        return False

    @property
    def byte_length(self):
        """
        Returns the size of this BitVector object in bytes.

        :return: the size in bytes of this BitVector object.
        """
        return self._byte_size

    def get(self, bit: int) -> int:
        """
        Getter function returning the value of a single bit in this BitVector.

        :param bit: an integer representing the index of a BitVector.
        :return: the value at the BitVector index, 0 or 1.
        """
        byte_index = bit // 8
        bit_index = bit & 0x7

        return (self._buffer[byte_index] >> bit_index) & 0x1

    def set(self, bit: int, value: int):
        """
        Setter function that sets a value of 0 or 1 at an index of the BitVector.

        :param bit: an integer representing an index of a BitVector.
        :param value: one or zero.
        """
        assert 0 <= value <= 1
        byte_index = bit // 8
        bit_index = bit & 0x7
        self._buffer[byte_index] |= (value & 0x1) << bit_index

    def as_binary(self):
        """
        Converts this BitVector object into a binary string.

        :return: binary string representation of this BitVector.
        """
        output = ''
        for n in bytes(self):
            output += ''.join(str(1 & (int(n) >> i)) for i in range(8)[::-1])
        return output

    def as_hex(self):
        """
        Converts this BitVector object into a hexadecimal string.

        :return: string of binary representation of this BitVector.
        """
        return binascii.hexlify(bytes(self)).decode()
