import unittest
from unittest import mock
from unittest.mock import patch

from fetchai.ledger.api import LedgerApi, ContractsApi
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity
from fetchai.ledger.serialisation.shardmask import ShardMask

CONTRACT_TEXT = """
@init
function init(owner: Address)
endfunction

@action
function action1()
endfunction

@action
function action2()
endfunction

@query
function query1()
endfunction

@query
function query2()
endfunction
"""

MULTIPLE_INITS = """
@init
function setup(owner: Address)
endfunction

@init
function alternative(owner: Address)
endfunction
"""

NO_INIT = """
@action
function action1()
endfunction
"""


class ContractTests(unittest.TestCase):
    def test_dumps_and_loads(self):
        owner = Entity()
        orig = Contract(CONTRACT_TEXT, owner, b'this is a nonce')

        # encode the contract
        encoded = orig.dumps()

        # re-create the contract
        new = Contract.loads(encoded)

        # checks
        self.assertIsInstance(new, Contract)
        self.assertEqual(orig.owner, new.owner)
        self.assertEqual(orig.digest, new.digest)
        self.assertEqual(orig.source, new.source)

    def test_dumps_and_loads_without_nonce(self):
        owner = Entity()
        orig = Contract(CONTRACT_TEXT, owner)

        # encode the contract
        encoded = orig.dumps()

        # re-create the contract
        new = Contract.loads(encoded)

        # checks
        self.assertIsInstance(new, Contract)
        self.assertEqual(orig.owner, new.owner)
        self.assertEqual(orig.digest, new.digest)
        self.assertEqual(orig.source, new.source)
        self.assertEqual(orig.nonce, new.nonce)

    @patch.object(ShardMask, 'resources_to_shard_mask')
    def test_create(self, mock_shard_mask):
        # create contract
        owner = Entity()
        contract = Contract(CONTRACT_TEXT, owner)

        # Mock api for providing number of lanes and receiving create call
        api = mock.Mock(spec=LedgerApi)
        api.server = mock.Mock()
        lane_number = 2
        api.server.num_lanes.side_effect = [lane_number]
        api.contracts = mock.Mock(spec=ContractsApi)

        # Mock shard mask static method
        dummy_shard_mask = mock.Mock()
        mock_shard_mask.side_effect = [dummy_shard_mask]

        contract.create(api, owner, 1000)

        # Check shard mask gen called with contract digest address
        mock_shard_mask.assert_called_once_with(
            ['fetch.contract.state.{}'.format(contract.digest.to_hex())], lane_number)
        # Check api create method called
        api.contracts.create.assert_called_once_with(owner, contract, 1000, shard_mask=dummy_shard_mask)

    def test_init(self):
        # Test rejection of contract with multiple init statements
        owner = Entity()
        with self.assertRaises(RuntimeError):
            contract = Contract(MULTIPLE_INITS, owner)

        # Test successful creation without init (to support local etch testing)
        try:
            contract = Contract(NO_INIT, owner)
        except Exception:
            self.fail("Contract initialisation with @init failed")

        # Test creation failure without init
        api = mock.Mock()
        with self.assertRaises(RuntimeError):
            contract.create(api, owner, 100)
