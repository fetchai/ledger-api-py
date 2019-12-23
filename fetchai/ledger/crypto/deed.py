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
            del self._thresholds[str(operation)]
            return

        if threshold > self.total_votes:
            raise InvalidDeedError("Attempting to set threshold higher than available votes - it will never be met")

        self._thresholds[str(operation)] = int(threshold)

    def remove_threshold(self, operation: Operation):
        if str(operation) in self._thresholds:
            del self._signees[str(operation)]

    def return_threshold(self, operation: Operation):
        return self._thresholds[str(operation)] if  \
            str(operation) in self._thresholds else None

    @property
    def total_votes(self):
        return sum(v for v in self._signees.values())

    @property
    def allow_no_amend(self):
        return self._allow_no_amend

    @property
    def amend_threshold(self):
        return self._thresholds['amend'] if \
            'amend' in self._thresholds else None

    @amend_threshold.setter
    def amend_threshold(self, value):
        self.set_threshold(Operation.amend, value)

    def deed_creation_json(self):
        deed = {
            'signees': {Address(k)._display: v for k, v in self._signees.items()},
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
            if key == 'amend':
                continue
            deed['thresholds'][key] = self._thresholds[key]

        return deed

    @classmethod
    def deed_from_json(cls, json_deed, allow_no_amend=False):
        if isinstance(json_deed, str):
            json_deed = json.loads(json_deed)


        print(json_deed)

        deed = Deed(allow_no_amend=allow_no_amend)

        signees = json_deed['signees']
        for signee, voting_weight in signees.items():
            deed.set_signee(Address(signee), voting_weight)

        thresholds = json_deed['thresholds']
        for operation, threhold in thresholds.items():
            deed.set_threshold(Operation[operation], threhold)

        if deed.amend_threshold:
            # Error if amend threshold un-meetable
            if deed.amend_threshold > deed.total_votes:
                raise InvalidDeedError("Amend threshold greater than total voting power - future amendment will be impossible")

        # Warnings/errors if no amend threshold set
        elif deed.allow_no_amend:
            logging.warning("Creating deed without amend threshold - future amendment will be impossible")
        else:
            raise InvalidDeedError("Creating deed without amend threshold - future amendment will be impossible")

        return deed

