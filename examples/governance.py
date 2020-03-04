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

from getpass import getpass

from pocketbook.key_store import KeyStore

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.api.governance import GovernanceProposal
from fetchai.ledger.crypto import Address


def get_miner_private_key(pocketbook_key_name: str, password: str = None):
    password = getpass(prompt='Password for key {}: '.format(pocketbook_key_name)) \
        if password is None \
        else password

    ks = KeyStore()

    return ks.load_key(
        pocketbook_key_name,
        password)


def main():
    entity1 = get_miner_private_key('my_miner_wallet')
    address1 = Address(entity1)
    api = LedgerApi('127.0.0.1', 8000)

    current_gov_proposals = api.governance.get_proposals()

    if current_gov_proposals.free_slots_in_queue == 0:
        raise RuntimeError('No room in queue - try again when a proposal currently in flight expires or is rejected')

    block_number = api.tokens.current_block_number()

    proposal_data = {
        'charge_multiplier': 42
    }

    proposal = GovernanceProposal(0, block_number + 50000, proposal_data)

    propose_tx = api.governance.propose(proposal, entity1, 10000)
    api.sync(propose_tx)

    # Need to cast a vote, as submitting a proposal does not implicitly do so
    accept_tx = api.governance.accept(proposal, entity1, 10000)
    api.sync(accept_tx)


if __name__ == '__main__':
    main()
