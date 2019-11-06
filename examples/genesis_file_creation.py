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

#
# How to create a genesis file for the network, setting up wealth for a number of entities and also the
# initial miners
#

from fetchai.ledger.crypto import Entity
from fetchai.ledger.genesis import *

def main():

    # Wealth division
    TOTAL_TOKEN_SUPPLY      = 11529975750000000000
    DESIRED_ENTITIES        = 30
    DESIRED_MINERS          = 20
    TOKENS_PER_ENTITY       = TOTAL_TOKEN_SUPPLY/DESIRED_ENTITIES
    TOKENS_STAKED_PER_MINER = TOKENS_PER_ENTITY/2

    # System parameters
    MAX_CABINET_SIZE   = 30
    BLOCK_INTERVAL_MS  = 1000
    START_IN_X_SECONDS = 5

    # Note: the first N of these will be miners
    print("Generating entities. This may take some time.")
    initial_entities = [(Entity(), TOKENS_PER_ENTITY, TOKENS_STAKED_PER_MINER if x < DESIRED_MINERS else 0) for x in range(DESIRED_ENTITIES)]
    print("Done.")

    genesis_file = GenesisFile(initial_entities, MAX_CABINET_SIZE, START_IN_X_SECONDS, BLOCK_INTERVAL_MS)

    genesis_file.dump_to_file("genesis_file.json")

if __name__ == '__main__':
    main()
