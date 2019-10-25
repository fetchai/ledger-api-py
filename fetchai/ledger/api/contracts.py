import logging
from typing import List

import msgpack

from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Address, Entity
from fetchai.ledger.serialisation import encode_transaction
from fetchai.ledger.transaction import Transaction
from .common import ApiEndpoint

EntityList = List[Entity]


class ContractsApi(ApiEndpoint):
    API_PREFIX = 'fetch.contract'

    def create(self, owner: Entity, contract: 'Contract', fee: int, shard_mask: BitVector = None):
        ENDPOINT = 'create'

        logging.debug('Deploying contract', contract.address)

        # Default to wildcard shard mask if none supplied
        if not shard_mask:
            logging.warning("Defaulting to wildcard shard mask as none supplied")
            shard_mask = BitVector()

        # build up the basic transaction information
        tx = self._create_skeleton_tx(fee)
        tx.from_address = Address(owner)
        tx.target_chain_code(self.API_PREFIX, shard_mask)
        tx.action = ENDPOINT
        tx.data = self._encode_json({
            'nonce': contract.nonce,
            'text': contract.encoded_source,
            'digest': contract.digest.to_hex()
        })
        tx.add_signer(owner)

        # encode and sign the transaction
        encoded_tx = encode_transaction(tx, [owner])

        # update the contracts owner
        contract.owner = owner

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def submit_data(self, entity: Entity, contract_digest: Address, contract_address: Address, **kwargs):
        # build up the basic transaction information
        tx = Transaction()
        tx.from_address = Address(entity)
        tx.valid_until = 10000
        tx.target_contract(contract_digest, contract_address, BitVector())
        tx.charge_rate = 1
        tx.charge_limit = 1000000000000
        tx.action = 'data'
        tx.synergetic_data_submission = True
        tx.data = self._encode_json(dict(**kwargs))
        tx.add_signer(entity)

        # encode the transaction
        encoded_tx = encode_transaction(tx, [entity])

        # submit the transaction to the catch-all endpoint
        return self._post_tx_json(encoded_tx, None)

    def query(self, contract_digest: Address, contract_owner: Address, query: str, **kwargs):
        prefix = '{}.{}'.format(contract_digest.to_hex(), str(contract_owner))
        return self._post_json(query, prefix=prefix, data=self._encode_json_payload(**kwargs))

    def action(self, contract_digest: Address, contract_address: Address, action: str,
               fee: int, from_address: Address, signers: EntityList,
               *args, shard_mask: BitVector = None):
        # Default to wildcard shard mask if none supplied
        if not shard_mask:
            logging.warning("Defaulting to wildcard shard mask as none supplied")
            shard_mask = BitVector()

        # build up the basic transaction information
        tx = self._create_skeleton_tx(fee)
        tx.from_address = Address(from_address)
        tx.target_contract(contract_digest, contract_address, shard_mask)
        tx.action = str(action)
        tx.data = self._encode_msgpack_payload(*args)

        for signer in signers:
            tx.add_signer(signer)

        encoded_tx = encode_transaction(tx, signers)

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
        for type in (bool, int, float, str):
            if isinstance(value, type):
                return True
        return False

    @staticmethod
    def _clean_items(**kwargs):
        for key, value in kwargs.items():
            if key.endswith('_'):
                key = key[:-1]
            yield key, value
