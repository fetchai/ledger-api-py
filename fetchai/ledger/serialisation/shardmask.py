import hashlib
import struct
from math import log2

from fetchai.ledger.bitvector import BitVector


class ShardMask:
    @classmethod
    def state_to_address(cls, state, contract):
        # TODO: note circular dependency, as this will be called by contract
        assert contract.owner, "Contract does not have an owner"
        return "{}.{}.state.{}".format(contract.digest.to_hex(), contract.owner, state)

    @classmethod
    def resources_to_shard_mask(cls, resource_addresses, num_lanes):
        shards = [cls.resource_to_shard(ra, num_lanes) for ra in resource_addresses]
        return BitVector.from_indices(shards, num_lanes)

    @staticmethod
    def resource_to_shard(resource_address, num_lanes):
        assert ((num_lanes & (num_lanes-1)) == 0) and num_lanes > 0, "Expecting power of two number of lanes"

        # SHA256 hash of resource_address
        s = hashlib.sha256()
        s.update(resource_address.encode('ascii'))

        # -> Resource ID
        resource_id = s.digest()

        # Take last 4 bytes
        group = struct.unpack('<I', resource_id[:4])[0]

        # modulo number of lanes
        shard = group & (num_lanes - 1)
        return shard
