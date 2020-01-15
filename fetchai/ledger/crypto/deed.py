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
import logging
from enum import Enum
from typing import Union
import json

from fetchai.ledger.crypto import Address, Identity, Entity

AddressLike = Union[Address, Identity]


class InvalidDeedError(Exception):
    pass


class Operation(Enum):
    """Enables future amendments to the deed"""
    amend = 1
    """Enables FET transfers"""
    transfer = 2
    """Enable execution of contract"""
    execute = 3
    """Enables operations related to staking"""
    stake = 4

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

    def __str__(self):
        return self.name


class Deed:
    def __init__(self, allow_no_amend: bool = False):
        self._allow_no_amend = allow_no_amend
        self._signees = {}
        self._thresholds = {}

    def __eq__(self, other: 'Deed'):
        if self is other:
            return True

        return other is not None and self._signees == other._signees and self._thresholds == other._thresholds and \
               self._allow_no_amend == other._allow_no_amend

    def __ne__(self, other: 'Deed'):
        return not self == other

    def set_signee(self, signee: AddressLike, voting_weight: int):
        if not isinstance(signee, Address):
            signee = Address(signee)

        if voting_weight is None and signee in self._signees:
            del self._signees[signee]
            return

        self._is_voting_weight_sane(signee, voting_weight, throw=True)
        self._signees[signee] = int(voting_weight)

    def get_signee(self, signee: AddressLike):
        if not isinstance(signee, Address):
            signee = Address(signee)

        return self._signees[signee] if signee in self._signees else None

    def set_threshold(self, operation: Operation, threshold: int):
        if threshold is None and operation in self._thresholds:
            del self._thresholds[operation]
            return

        self._is_threshold_sane(operation, threshold, throw=True)
        self._thresholds[operation] = int(threshold)

    def get_threshold(self, operation: Operation):
        return self._thresholds[operation] if operation in self._thresholds else None

    @property
    def signees(self):
        for signee, voting_weight in self._signees.items():
            yield signee, voting_weight

    @property
    def thresholds(self):
        for operation, threshold in self._thresholds.items():
            yield operation, threshold

    @property
    def total_votes(self):
        return sum(v for v in self._signees.values())

    @property
    def allow_no_amend(self):
        return self._allow_no_amend

    def is_sane(self, throw: bool = False):
        if self.allow_no_amend:
            logging.warning("Creating deed without amend threshold - future amendment will be impossible")
        elif not self.allow_no_amend and Operation.amend not in self._thresholds:
            if throw:
                raise InvalidDeedError("The '{}' operation is mandatory but it not present".format(Operation.amend))
            return False

        for signee, voting_weight in self._signees.items():
            if not self._is_voting_weight_sane(signee, voting_weight, throw=throw):
                return False

        total_voting_weight = self.total_votes

        for operation, threshold in self._thresholds.items():
            if not self._is_threshold_sane(operation, threshold, throw=throw):
                return False
            elif threshold > total_voting_weight:
                if throw:
                    raise InvalidDeedError(
                        "Threshold value {} for '{}' operation is greater than total"
                        "voting weight {}".format(threshold, operation, total_voting_weight))
                return False

        return True

    def to_json(self, verify_sanity: bool = True):
        if verify_sanity:
            self.is_sane(throw=True)

        deed = {
            'signees': {str(Address(signee)): voting_weight for signee, voting_weight in self._signees.items()},
            'thresholds': {str(operation): threshold for operation, threshold in self._thresholds.items()}
        }

        return deed

    @classmethod
    def from_json(cls, json_deed, allow_no_amend: bool = False, verify_sanity: bool = True):
        if isinstance(json_deed, str):
            json_deed = json.loads(json_deed)

        deed = Deed(allow_no_amend=allow_no_amend)

        signees = json_deed['signees']
        for signee, voting_weight in signees.items():
            deed._signees[Address(signee)] = int(voting_weight)

        thresholds = json_deed['thresholds']
        for operation, threshold in thresholds.items():
            deed._thresholds[Operation[operation]] = int(threshold)

        if verify_sanity:
            deed.is_sane(throw=True)

        return deed

    @classmethod
    def _is_voting_weight_sane(cls, signee: Address, voting_weight: int, throw: bool = False):
        if voting_weight <= 0:
            if throw:
                raise InvalidDeedError("Invalid voting weight {} for the '{}' signee".format(voting_weight, signee))
            return False

        return True

    @classmethod
    def _is_threshold_sane(cls, operation: Operation, threshold: int, throw: bool = False):
        if threshold <= 0:
            if throw:
                raise InvalidDeedError("Invalid threshold value {} for the '{}' operation".format(threshold, operation))
            return False

        return True
