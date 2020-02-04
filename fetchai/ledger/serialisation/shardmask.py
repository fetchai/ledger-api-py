import struct
from typing import Iterable

from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.serialisation.sha256 import sha256_hash


class ShardMask:

    @staticmethod
    def state_to_address(address: str, variable: str) -> str:
        """
        Create fully qualified resource address from a contract address and variable name

        :param address: The name of the contract (main namespace)
        :param variable: The name of the variable being accessed
        :return: The generated resource address
        """
        return "{}.state.{}".format(address, variable)

    @classmethod
    def resources_to_shard_mask(cls, resource_addresses: Iterable[str], num_lanes: int) -> BitVector:
        """
        Converts a set resources addresses into a compatible shard mask

        :param resource_addresses: The iterable set of fully qualified resource addresses
        :param num_lanes: The number of lanes that are being targeted
        :return: The shard mask bit vector for shard allocation
        """
        shards = [cls.resource_to_shard(ra, num_lanes) for ra in resource_addresses]
        return BitVector.from_indices(shards, num_lanes)

    @staticmethod
    def resource_to_shard(resource_address: str, num_lanes: int) -> int:
        """
        Converts a fully qualified resource address into a shard index

        :param resource_address: The resource address to be updated
        :param num_lanes: The number of lanes that are being targetted
        :return: The shard index for this resource
        """

        assert ((num_lanes & (num_lanes - 1)) == 0) and num_lanes > 0, "Expecting power of two number of lanes"

        # Resource ID from address
        resource_id = sha256_hash(resource_address.encode('ascii'))

        # Take last 4 bytes
        group = struct.unpack('<I', resource_id[:4])[0]

        # modulo number of lanes
        shard = group & (num_lanes - 1)
        return shard
