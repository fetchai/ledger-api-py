class BitVector:

    @staticmethod
    def from_bytes(data: bytes, bit_size: int):

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
        decoded_bytes = bytes.fromhex(hex_data)
        return cls.from_bytes(decoded_bytes, len(decoded_bytes) * 8)

    @staticmethod
    def from_array(bit_array: list):
        bits = BitVector(len(bit_array))
        for i, v in enumerate(reversed(bit_array)):
            if v:
                bits.set(i, True)
        return bits

    @staticmethod
    def from_indices(indices: list, size: int):
        bits = BitVector(size)
        for i in indices:
            assert 0 <= i < size, "Index exceeds list size"
            bits.set(i, True)
        return bits

    def __init__(self, size=None):
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
        return bytes(reversed(self._buffer))

    def __len__(self):
        return self._size

    def __eq__(self, other):
        if len(self) == len(other):
            return bytes(self) == bytes(other)
        return False

    @property
    def byte_length(self):
        return self._byte_size

    def get(self, bit: int) -> int:
        byte_index = bit // 8
        bit_index = bit & 0x7

        return (self._buffer[byte_index] >> bit_index) & 0x1

    def set(self, bit: int, value: int):
        assert 0 <= value <= 1
        byte_index = bit // 8
        bit_index = bit & 0x7
        self._buffer[byte_index] |= (value & 0x1) << bit_index

    def as_binary(self):
        output = ''
        for n in bytes(self):
            output += ''.join(str(1 & (int(n) >> i)) for i in range(8)[::-1])
        return output

    def as_hex(self):
        return bytes(self).hex()
