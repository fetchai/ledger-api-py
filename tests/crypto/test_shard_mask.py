import unittest
from unittest import mock

from fetchai.ledger.serialisation.shardmask import ShardMask


class TestShardMask(unittest.TestCase):
    def test_state_to_address(self):
        contract = mock.Mock()
        contract.digest.to_hex.side_effect = ['abc']
        contract.owner = 'def'

        address = ShardMask.state_to_address('xyz', contract)
        self.assertEqual(address, 'abc.def.state.xyz')

    def test_resource_to_shard(self):
        # Test rejection of invalid lane number
        with self.assertRaises(AssertionError):
            ShardMask.resource_to_shard('abc', 3)

        # Test known addresses
        addresses = ['abc', 'def', 'XYZ']
        shards = [2, 3, 1]

        for add, sh in zip(addresses, shards):
            self.assertEqual(ShardMask.resource_to_shard(add, 4), sh)

        # Repeat for different lane number, expect different results
        addresses = ['abc', 'def', 'XYZ']
        shards = [10, 11, 13]

        for add, sh in zip(addresses, shards):
            self.assertEqual(ShardMask.resource_to_shard(add, 16), sh)

    def test_resource_to_shard_mask(self):
        num_lanes = 4
        bv = ShardMask.resources_to_shard_mask(['abc', 'def', 'XYZ'], num_lanes)
        self.assertEqual(bv._size, num_lanes)
        self.assertEqual(bv.as_binary(), '00001110')
