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
    """Enab"""
    execute = 3

    stake = 4

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

    def __str__(self):
        return self.name


class Deed:
    def __init__(self, allow_no_amend=False):
        self._allow_no_amend = allow_no_amend
        self._signees = {}
        self._thresholds = {}

    def set_signee(self, signee: Entity, voting_weight: int):
        self._signees[signee] = int(voting_weight)

    def remove_signee(self, signee: Entity):
        if signee in self._signees:
            del self._signees[signee]

    def set_threshold(self, operation: Operation, threshold: int):
        if threshold is None:
            del self._thresholds[operation]
            return

        if threshold > self.total_votes:
            raise InvalidDeedError("Attempting to set threshold higher than available votes - it will never be met")

        self._thresholds[operation] = int(threshold)

    def remove_threshold(self, operation: Operation):
        if operation in self._thresholds:
            del self._thresholds[operation]

    def return_threshold(self, operation: Operation):
        return self._thresholds[operation] if operation in self._thresholds else None

    @property
    def total_votes(self):
        return sum(v for v in self._signees.values())

    @property
    def allow_no_amend(self):
        return self._allow_no_amend

    def is_sane(self, throw=False):
        if self.allow_no_amend and Operation.amend not in self._thresholds:
            if throw:
                raise InvalidDeedError("The '{}' operation is required but it not present".format(Operation.amend))

            return False

        for signee, voting_weight in self._signees.items():
            if voting_weight <= 0:
                if throw:
                    raise InvalidDeedError("Invalid voting weight {} for signee '{}'".format(voting_weight, signee))

                return False

        total_voting_weight = self.total_votes

        for operation, threshold in self._thresholds.items():
            if threshold > total_voting_weight:
                if throw:
                    raise InvalidDeedError(
                        "Threshold value {} for '{}' operation is greater than total"
                        "voting weight {}".format(threshold, operation, total_voting_weight))

                return False

        return True

    def deed_creation_json(self):
        self.is_sane(throw=True)

        deed = {
            'signees': {str(Address(k)): v for k, v in self._signees.items()},
            'thresholds': {}
        }

        if self.amend_threshold:
            # Error if amend threshold un-meetable
            if self.amend_threshold > self.total_votes:
                raise InvalidDeedError(
                    "Amend threshold greater than total voting power - future amendment will be impossible")

            deed['thresholds']['amend'] = self.amend_threshold

        # Warnings/errors if no amend threshold set
        elif self.allow_no_amend:
            logging.warning("Creating deed without amend threshold - future amendment will be impossible")
        else:
            raise InvalidDeedError("Creating deed without amend threshold - future amendment will be impossible")

        # Add other thresholds
        for key in self._thresholds:
            if key == Operation.amend:
                continue
            deed['thresholds'][key] = self._thresholds[key]

        return deed

    @classmethod
    def deed_from_json(cls, json_deed, allow_no_amend=False, verify_sanity=True):
        if isinstance(json_deed, str):
            json_deed = json.loads(json_deed)

        deed = Deed(allow_no_amend=allow_no_amend)

        signees = json_deed['signees']
        for signee, voting_weight in signees.items():
            if verify_sanity:
                deed.set_signee(Address(signee), voting_weight)
            else:
                deed._signees[Address(signee)] = int(voting_weight)

        thresholds = json_deed['thresholds']
        for operation, threshold in thresholds.items():
            if verify_sanity:
                deed.set_threshold(Operation[operation], threshold)
            else:
                deed._thresholds[Operation[operation]] = threshold

        if verify_sanity:
            deed.is_sane(throw=True)

        return deed

