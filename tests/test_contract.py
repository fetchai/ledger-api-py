import unittest
from unittest import mock
from unittest.mock import patch

from fetchai.ledger.api import LedgerApi, ContractsApi
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity
from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.serialisation.shardmask import ShardMask

CONTRACT_TEXT = """
persistent sharded value_ : Int64;

@init
function init(owner: Address)
endfunction

@action
function action1(arg1: String, arg2: String)
    use value[arg1, arg2];
   
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
            ['fetch.contract.state.{}'.format(str(contract.address))], lane_number)
        # Check api create method called
        api.contracts.create.assert_called_once_with(owner, contract, 1000, shard_mask=dummy_shard_mask)


    @patch.object(ShardMask, 'resources_to_shard_mask')
    def test_action(self, mock_shard_mask):
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

        contract.action(api, 'action1', 1000, owner, 'arg1', 'arg2')

        # Check shard mask gen called with contract digest address
        base_contract_address = 'fetch.contract.state.{}'.format(str(contract.address))
        expected_resources = [
            base_contract_address,
            '{}.value_.arg1'.format(base_contract_address),
            '{}.value_.arg2'.format(base_contract_address),
        ]

        # TODO: Due to parser errors the contract can not correctly distinguish the bit vectors. This means a wild card
        #       bit vector is used.
        #mock_shard_mask.assert_called_once_with(expected_resources, lane_number)


        # Check api create method called
        api.contracts.action.assert_called_once_with(contract.address, 'action1', 1000, owner, 'arg1', 'arg2',
                                                     shard_mask=BitVector())


    def test_init_fail_multiple_inits(self):
        # Test rejection of contract with multiple init statements
        owner = Entity()
        with self.assertRaises(RuntimeError):
            _ = Contract(MULTIPLE_INITS, owner)

    @patch.object(ShardMask, 'resources_to_shard_mask')
    def test_create_without_init(self, mock_shard_mask):
        owner = Entity()
        contract = Contract(NO_INIT, owner)

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
            ['fetch.contract.state.{}'.format(str(contract.address))], lane_number)

        # Check api create method called
        api.contracts.create.assert_called_once_with(owner, contract, 1000, shard_mask=dummy_shard_mask)

    def test_single_entity_conversion(self):
        entity = Entity()
        self.assertEqual(entity, Contract._convert_to_single_entity(entity))

    def test_set_single_entity_conversion(self):
        entity = Entity()
        self.assertEqual(entity, Contract._convert_to_single_entity({entity}))

    def test_list_single_entity_conversion(self):
        entity = Entity()
        self.assertEqual(entity, Contract._convert_to_single_entity([entity]))

    def test_dict_single_entity_conversion(self):
        entity = Entity()
        self.assertEqual(entity, Contract._convert_to_single_entity({entity: None}))

    def test_error_when_multiple_values_provided(self):
        with self.assertRaises(ValueError):
            Contract._convert_to_single_entity([Entity(), Entity()])

    def test_error_when_type_is_wrong(self):
        with self.assertRaises(ValueError):
            Contract._convert_to_single_entity([None])

    def test_error_with_non_iterable_type(self):
        with self.assertRaises(ValueError):
            Contract._convert_to_single_entity(None)
