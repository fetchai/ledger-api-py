# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

import base64
from typing import Iterable, Callable

from fetchai.ledger.api import ApiEndpoint
from fetchai.ledger.api.common import TransactionFactory, ApiError
from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Address, Entity, Identity

GOVERNANCE_API_PREFIX = 'fetch.governance'

GovTxFactory = Callable[[Address, int, Iterable[Identity], 'GovernanceProposal'], 'Transaction']


class GovernanceProposal:
    def __init__(self, version: int, accept_by: int, data: dict):
        self.version = version
        self.accept_by = accept_by
        self.data = data

        self._validate()

    @classmethod
    def from_dict(cls, data: dict):
        return GovernanceProposal(data['version'], data['accept_by'], data['data'])

    def to_dict(self):
        return {
            'version': self.version,
            'accept_by': self.accept_by,
            'data': self.data
        }

    def _assert_prop(self, key_, type_):
        if key_ not in self.data or not isinstance(self.data[key_], type_):
            raise ApiError('Version {} proposal data must contain property \'{}\' of type {}' \
                           .format(self.version, key_, type_.__name__))

    def _validate(self):
        if self.version == 0:
            CHARGE_MULTIPLIER_KEY = 'charge_multiplier'

            self._assert_prop(CHARGE_MULTIPLIER_KEY, int)
        else:
            raise ApiError('Unrecognised proposal version {}'.format(self.version))


class CurrentGovernanceProposals:
    def __init__(self, active_proposal: GovernanceProposal, voting_queue: Iterable[GovernanceProposal],
                 max_number_of_proposals: int):
        self.active_proposal = active_proposal
        self.voting_queue = voting_queue

        # Subtract one to account for currently active proposal
        self.free_slots_in_queue = max_number_of_proposals - 1


class GovernanceApi(ApiEndpoint):
    API_PREFIX = GOVERNANCE_API_PREFIX

    def _send_gov_tx(self, factory: GovTxFactory, name: str, fee: int, signer: Entity, proposal: GovernanceProposal):
        tx = factory(Address(signer), fee, [signer], proposal)

        self._set_validity_period(tx)
        tx.sign(signer)

        return self._post_tx_json(tx, name)

    def propose(self, proposal: GovernanceProposal, signer: Entity, fee: int):
        """
        Send a governance proposal.

        :param from_address: The proposal issuer
        :param fee: The maximum fee
        :param signer: The entities that will sign this action
        :param proposal: The governance proposal
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        return self._send_gov_tx(GovernanceTxFactory.propose, 'propose', fee, signer, proposal)

    def accept(self, proposal: GovernanceProposal, signer: Entity, fee: int):
        """
        Accept a governance proposal.

        :param from_address: The proposal issuer
        :param fee: The maximum fee
        :param signer: The entities that will sign this action
        :param proposal: The governance proposal
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        return self._send_gov_tx(GovernanceTxFactory.accept, 'accept', fee, signer, proposal)

    def reject(self, proposal: GovernanceProposal, signer: Entity, fee: int):
        """
        Reject a governance proposal.

        :param from_address: The proposal issuer
        :param fee: The maximum fee
        :param signer: The entities that will sign this action
        :param proposal: The governance proposal
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        return self._send_gov_tx(GovernanceTxFactory.reject, 'reject', fee, signer, proposal)

    def get_proposals(self) -> CurrentGovernanceProposals:
        """
        Query the governance proposals currently present in the system.

        :return: a CurrentGovernanceProposals object
        :raises: ApiError on any failures
        """

        success, data = self._post_json('get_proposals')

        # check for error cases
        if not success:
            raise ApiError('Failed to query proposals')

        if not ('active_proposal' in data and 'voting_queue' in data and 'max_number_of_proposals' in data):
            raise ApiError('Malformed response from server')

        active_proposal = data['active_proposal']
        voting_queue = data['voting_queue']
        max_number_of_proposals = data['max_number_of_proposals']

        return CurrentGovernanceProposals(
            GovernanceProposal.from_dict(active_proposal),
            [GovernanceProposal.from_dict(prop) for prop in voting_queue],
            max_number_of_proposals)


class GovernanceTxFactory(TransactionFactory):
    API_PREFIX = GOVERNANCE_API_PREFIX

    @classmethod
    def _construct_gov_tx(cls, tx_endpoint: str, from_address: Address, fee: int,
                          signatories: Iterable[Identity], proposal: GovernanceProposal) -> 'Transaction':
        shard_mask = BitVector()

        tx = cls._create_chain_code_action_tx(fee, from_address, tx_endpoint, signatories, shard_mask)

        tx.data = base64.b64encode(cls._encode_json(proposal.to_dict()))

        return tx

    @classmethod
    def propose(cls, from_address: Address, fee: int,
                signatories: Iterable[Identity], proposal: GovernanceProposal) -> 'Transaction':
        return cls._construct_gov_tx('propose', from_address, fee, signatories, proposal)

    @classmethod
    def accept(cls, from_address: Address, fee: int,
               signatories: Iterable[Identity], proposal: GovernanceProposal) -> 'Transaction':
        return cls._construct_gov_tx('accept', from_address, fee, signatories, proposal)

    @classmethod
    def reject(cls, from_address: Address, fee: int,
               signatories: Iterable[Identity], proposal: GovernanceProposal) -> 'Transaction':
        return cls._construct_gov_tx('reject', from_address, fee, signatories, proposal)
