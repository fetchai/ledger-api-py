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

    print("Generating entities. This may take some time.")
    initial_entities = [(Entity(), TOKENS_PER_ENTITY) for x in range(DESIRED_ENTITIES)]
    print("Done.")

    # the first N of these will be miners
    initial_miners = [(initial_entities[x][0], TOKENS_STAKED_PER_MINER) for x in range(DESIRED_MINERS)]

    #import ipdb; ipdb.set_trace(context=20)

    genesis_file = GenesisFile(initial_entities, initial_miners, MAX_CABINET_SIZE, START_IN_X_SECONDS, BLOCK_INTERVAL_MS)

    import ipdb; ipdb.set_trace(context=20)

    aa = genesis_file.as_json()

    #genesis_file.dump_to_file()

    import ipdb; ipdb.set_trace(context=20)

    ## create the APIs
    #api = LedgerApi(HOST, PORT)

    ## generate a random identity
    #your_identity = Entity()
    #other_identity = Entity()
    #print('Balance Before:', api.tokens.balance(your_identity))

    ## create the balance
    #print('Submitting wealth creation...')
    #api.sync(api.tokens.wealth(your_identity, 1000))
    #print('Balance after wealth:', api.tokens.balance(your_identity))

    ## submit and wait for the transfer to be complete
    #print('Submitting transfer...')
    #api.sync(api.tokens.transfer(your_identity, other_identity, 250, 20))

    #print('Balance 1:', api.tokens.balance(your_identity))
    #print('Balance 2:', api.tokens.balance(other_identity))


if __name__ == '__main__':
    main()
