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
import json
import logging
from enum import Enum
from typing import Union, Dict

from fetchai.ledger.crypto import Address, Identity

AddressLike = Union[Address, Identity, str]


class InvalidDeedError(Exception):
    pass


def _one_or_greater(value):
    value = int(value)
    if value <= 0:
        raise ValueError('Value {} should be greater or equal to 1'.format(value))
    return value


class Operation(Enum):
    """Enables future amendments to the deed"""
    amend = 1
    """Enables FET transfers"""
    transfer = 2
    """Enab"""
    execute = 3

    stake = 4

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

    def __str__(self):
        return self.name


class Deed:
    def __init__(self):
        self._signees = {}  # type: Dict[Address, int]
        self._thresholds = {}  # type: Dict[Operation, int]
        self._required_amend = True  # type: bool

    def __eq__(self, other: 'Deed'):
        if self is other:
            return True

        return other is not None and self._signees == other._signees and self._thresholds == other._thresholds

    def __ne__(self, other: 'Deed'):
        return not self == other

    @property
    def signees(self):
        return set(self._signees.keys())

    @property
    def votes(self):
        return self._signees.items()

    @property
    def operations(self):
        return set(self._thresholds.keys())

    @property
    def thresholds(self):
        return self._thresholds.items()

    @property
    def total_votes(self):
        return sum(v for v in self._signees.values())

    @property
    def require_amend(self):
        return self._required_amend

    @require_amend.setter
    def require_amend(self, value: bool):
        self._required_amend = bool(value)

    def get_signee(self, signee: AddressLike):
        signee = Address(signee)

        return self._signees.get(signee)

    def set_signee(self, signee: AddressLike, voting_weight: int):
        signee = Address(signee)
        voting_weight = _one_or_greater(voting_weight)

        self._signees[signee] = int(voting_weight)

    def remove_signee(self, signee: AddressLike):
        signee = Address(signee)
        if signee in self._signees:
            del self._signees[signee]

    def set_operation(self, operation: Operation, threshold: int):
        threshold = _one_or_greater(threshold)

        self._thresholds[operation] = int(threshold)

    def remove_operation(self, operation: Operation):
        if operation in self._thresholds:
            del self._thresholds[operation]

    def get_threshold(self, operation: Operation):
        return self._thresholds[operation] if operation in self._thresholds else None

    def validate(self):
        if not self.require_amend:
            logging.warning("Creating deed without amend threshold - future amendment will be impossible")
        elif Operation.amend not in self._thresholds:
            raise InvalidDeedError("The '{}' operation is mandatory but it not present".format(Operation.amend))

        # cache the total voting weight
        total_voting_weight = self.total_votes

        for operation, threshold in self._thresholds.items():
            if threshold > total_voting_weight:
                raise InvalidDeedError(
                    "Threshold value {} for '{}' operation is greater than total voting weight {}".format(
                        threshold, operation, total_voting_weight))

    def to_json(self):
        self.validate()

        return {
            'signees': {str(Address(signee)): voting_weight for signee, voting_weight in self._signees.items()},
            'thresholds': {str(operation): threshold for operation, threshold in self._thresholds.items()}
        }

    @classmethod
    def from_json(cls, json_deed, require_amend: bool = True):
        if isinstance(json_deed, str):
            json_deed = json.loads(json_deed)

        deed = Deed()
        deed.require_amend = bool(require_amend)

        signees = json_deed['signees']
        for signee, voting_weight in signees.items():
            deed._signees[Address(signee)] = int(voting_weight)

        thresholds = json_deed['thresholds']
        for operation, threshold in thresholds.items():
            deed._thresholds[Operation[operation]] = int(threshold)

        # ensure that the deed is valid
        deed.validate()

        return deed
