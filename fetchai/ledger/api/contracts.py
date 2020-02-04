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
import logging
from typing import List, Optional, Iterable, Union

import msgpack

from fetchai.ledger.api.common import TransactionFactory
from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Address, Entity, Identity
from fetchai.ledger.serialisation import transaction
from fetchai.ledger.transaction import Transaction
from .common import ApiEndpoint

EntityList = List[Entity]
AddressLike = Union[Address, str]


class ContractsApi(ApiEndpoint):
    API_PREFIX = 'fetch.contract'

    def create(self, owner: Entity, contract: 'Contract', fee: int, shard_mask: BitVector = None):
        ENDPOINT = 'create'

        logging.debug('Deploying contract', contract.address)

        tx = ContractTxFactory.create(Address(owner), contract, fee, [owner], shard_mask)
        self._set_validity_period(tx)
        tx.sign(owner)

        # encode and sign the transaction
        encoded_tx = transaction.encode_transaction(tx)

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def submit_data(self, entity: Entity, contract_address: Address, fee: int, **kwargs):
        # build up the basic transaction information
        tx = self._create_skeleton_tx(fee)
        self._set_validity_period(tx)
        tx.from_address = Address(entity)
        tx.target_synergetic_data(contract_address, BitVector())
        tx.action = 'data'
        tx.data = self._encode_json(dict(**kwargs))
        tx.add_signer(entity)
        tx.sign(entity)

        # encode the transaction
        encoded_tx = transaction.encode_transaction(tx)

        # submit the transaction to the catch-all endpoint
        return self._post_tx_json(encoded_tx, None)

    def query(self, contract_owner: Address, query: str, **kwargs):
        return self._post_json(query, prefix=str(contract_owner), data=self._encode_json_payload(**kwargs))

    def action(self, contract_address: Address, action: str, fee: int, signer: Entity, *args,
               from_address: Address = None, shard_mask: BitVector = None):

        tx = ContractTxFactory.action(from_address or Address(signer), contract_address, action, fee, [signer], *args,
                                      shard_mask=shard_mask)
        tx.data = self._encode_msgpack_payload(*args)
        self._set_validity_period(tx)
        tx.sign(signer)

        encoded_tx = transaction.encode_transaction(tx)

        return self._post_tx_json(encoded_tx, None)

    @classmethod
    def _encode_msgpack_payload(cls, *args):
        items = []
        for value in args:
            if cls._is_primitive(value):
                items.append(value)
            elif isinstance(value, Address):
                items.append(msgpack.ExtType(77, bytes(value)))
            else:
                raise RuntimeError('Unknown item to pack: ' + value.__class__.__name__)
        return msgpack.packb(items)

    @classmethod
    def _encode_json_payload(cls, **kwargs):
        params = {}
        for key, value in cls._clean_items(**kwargs):
            assert isinstance(key, str)  # should always be the case

            if cls._is_primitive(value):
                params[key] = value
            elif isinstance(value, Address):
                params[key] = str(value)
            elif isinstance(value, dict):
                params[key] = cls._encode_json_payload(**value)
            else:
                raise RuntimeError('Unknown item to pack: ' + value.__class__.__name__)
        return params

    @staticmethod
    def _is_primitive(value):
        for _type in (bool, int, float, str):
            if isinstance(value, _type):
                return True
        return False

    @staticmethod
    def _clean_items(**kwargs):
        for key, value in kwargs.items():
            if key.endswith('_'):
                key = key[:-1]
            yield key, value


class ContractTxFactory(TransactionFactory):
    API_PREFIX = 'fetch.contract'

    @classmethod
    def create(cls, from_address: AddressLike, contract: 'Contract', fee: int, signatories: Iterable[Identity],
               shard_mask: Optional[BitVector] = None) -> Transaction:

        # Default to wildcard shard mask if none supplied
        if not shard_mask:
            logging.warning("Defaulting to wildcard shard mask as none supplied")
            shard_mask = BitVector()

        # build up the basic transaction information
        tx = cls._create_chain_code_action_tx(fee, from_address, 'create', signatories, shard_mask)
        tx.data = cls._encode_json({
            'nonce': contract.nonce,
            'text': contract.encoded_source,
            'digest': contract.digest,
        })

        return tx

    @classmethod
    def action(cls, from_address: Address, contract_address: Address, action: str, fee: int, signers: List[Identity],
               *args, shard_mask: Optional[BitVector] = None) -> Transaction:

        # Default to wildcard shard mask if none supplied
        if not shard_mask:
            logging.warning("Defaulting to wildcard shard mask as none supplied")
            shard_mask = BitVector()

        # select the from address
        if from_address is None:
            if len(signers) == 1:
                from_address = Address(signers[0])
            else:
                raise RuntimeError('Unable to determine from field for transaction, more than 1 signer provided')

        # build up the basic transaction information
        tx = cls._create_smart_contract_action_tx(fee, from_address, contract_address, action, signers, shard_mask)
        tx.data = cls._encode_msgpack_payload(*args)

        return tx
