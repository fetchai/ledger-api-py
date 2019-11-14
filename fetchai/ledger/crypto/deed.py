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
from typing import Union

from fetchai.ledger.crypto import Address, Identity, Entity

AddressLike = Union[Address, Identity]

class Deed:
    def __init__(self, address: Entity):
        self._address = address
        self._amend_threshold = None
        self._transfer_threshold = None
        self._signees = {}

    def add_signee(self, signee: Entity, voting_weight: int):
        self._signees[signee] = voting_weight

    @property
    def amend_threshold(self):
        return self._amend_threshold

    @amend_threshold.setter
    def amend_threshold(self, value):
        self._amend_threshold = value

    @property
    def transfer_threshold(self):
        return self._transfer_threshold

    @transfer_threshold.setter
    def transfer_threshold(self, value):
        self._transfer_threshold = value

    def deed_creation_json(self):
        deed = {
            'address': Address(self._address)._display,
            'signees': {Address(k)._display: v for k, v in self._signees.items()},
            'thresholds': {}
        }

        if self._amend_threshold:
            deed['thresholds']['amend'] = self._amend_threshold
        else:
            logging.warning("Creating deed without amend threshold - future amendment will be impossible")

        if self._transfer_threshold:
            deed['thresholds']['transfer'] = self._transfer_threshold

        return deed
