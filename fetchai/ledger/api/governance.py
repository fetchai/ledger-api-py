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
from typing import Iterable, Sequence

from fetchai.ledger.api import ApiEndpoint
from fetchai.ledger.api.common import TransactionFactory, ApiError
from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Address, Entity, Identity

GOVERNANCE_API_PREFIX = 'fetch.governance'


class GovernanceProposal:
    def __init__(self, version: int, accept_by: int, data: dict):
        self.version = version
        self.accept_by = accept_by
        self.data = data

        self._validate()

    def _assert_prop(self, key_, type_):
        assert key_ in self.data and isinstance(self.data[key_], type_), \
            'Version {} proposal data must contain property \'{}\' of type {}' \
                .format(self.version, key_, type_.__name__)

    def _validate(self):
        if self.version == 0:
            CHARGE_MULTIPLIER_KEY = 'charge_multiplier'

            self._assert_prop(CHARGE_MULTIPLIER_KEY, int)

        else:
            raise ApiError('Unrecognised proposal version {}'.format(self.version))


class GovernanceApi(ApiEndpoint):
    API_PREFIX = GOVERNANCE_API_PREFIX

    def _send_gov_tx(self, factory, from_address: Address, fee: int, signatories: Sequence[Entity],
                     proposal: GovernanceProposal):
        assert len(signatories) == 1, \
            'Governance transactions should have a single signatory'
        assert from_address == Address(signatories[0]), \
            'Governance transactions should be signed and issued by the same miner'

        tx = factory(from_address, fee, signatories, proposal)

        self._set_validity_period(tx)
        [tx.sign(signer) for signer in signatories]

        return self.submit_signed_tx(tx)

    def propose(self, from_address: Address, fee: int, signatories: Sequence[Entity], proposal: GovernanceProposal):
        """
        Send a governance proposal.

        :param from_address: The proposal issuer
        :param fee: The maximum fee
        :param signatories: The entities that will sign this action
        :param proposal: The governance proposal
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        return self._send_gov_tx(GovernanceTxFactory.propose, from_address, fee, signatories, proposal)

    def accept(self, from_address: Address, fee: int, signatories: Sequence[Entity], proposal: GovernanceProposal):
        """
        Accept a governance proposal.

        :param from_address: The proposal issuer
        :param fee: The maximum fee
        :param signatories: The entities that will sign this action
        :param proposal: The governance proposal
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        return self._send_gov_tx(GovernanceTxFactory.accept, from_address, fee, signatories, proposal)

    def reject(self, from_address: Address, fee: int, signatories: Sequence[Entity], proposal: GovernanceProposal):
        """
        Reject a governance proposal.

        :param from_address: The proposal issuer
        :param fee: The maximum fee
        :param signatories: The entities that will sign this action
        :param proposal: The governance proposal
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        return self._send_gov_tx(GovernanceTxFactory.reject, from_address, fee, signatories, proposal)


class GovernanceTxFactory(TransactionFactory):
    API_PREFIX = GOVERNANCE_API_PREFIX

    @classmethod
    def _construct_gov_tx(cls, tx_endpoint: str, from_address: Address, fee: int,
                          signatories: Iterable[Identity], proposal: GovernanceProposal) -> 'Transaction':
        shard_mask = BitVector()

        tx = cls._create_chain_code_action_tx(fee, from_address, tx_endpoint, signatories, shard_mask)

        tx.data = base64.b64encode(cls._encode_json({
            'version': proposal.version,
            'accept_by': proposal.accept_by,
            'data': proposal.data
        }))

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