import unittest

from fetchai.ledger.crypto import Entity
from fetchai.ledger.genesis import GenesisFile

class EntityTests(unittest.TestCase):
    def test_json_generation(self):
        # Wealth division
        DESIRED_ENTITIES            = 30
        DESIRED_MINERS              = 20
        TOTAL_TOKEN_SUPPLY          = 1000000
        TOKENS_ALLOCATED_FOR_MINERS = 100
        TOKENS_STAKED_PER_MINER     = int(TOKENS_ALLOCATED_FOR_MINERS / DESIRED_MINERS)
        TOKENS_PER_ENTITY           = int((TOTAL_TOKEN_SUPPLY-(TOKENS_ALLOCATED_FOR_MINERS)) /DESIRED_ENTITIES)

        # System parameters
        MAX_CABINET_SIZE   = 30
        BLOCK_INTERVAL_MS  = 1000
        START_IN_X_SECONDS = 5

        initial_entities = [(Entity(), TOKENS_PER_ENTITY, TOKENS_STAKED_PER_MINER if x < DESIRED_MINERS else 0) for x in range(DESIRED_ENTITIES)]

        genesis_file = GenesisFile(initial_entities, MAX_CABINET_SIZE, START_IN_X_SECONDS, BLOCK_INTERVAL_MS)

        # Check that the structure is correct
        genesis_file_json = genesis_file.as_json_object()

        self.assertEqual(genesis_file_json['version'], 3)

        funds_all_accounts = 0
        stake_all_accounts = 0

        for account in genesis_file_json['accounts']:
            funds_all_accounts += account['balance']
            stake_all_accounts += account['stake']

        # Check that there are as many tokens as originally planned
        self.assertEqual(funds_all_accounts + stake_all_accounts, TOTAL_TOKEN_SUPPLY)
