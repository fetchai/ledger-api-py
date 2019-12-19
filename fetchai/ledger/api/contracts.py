import logging
from typing import List, Optional

import msgpack

from fetchai.ledger.api.common import TransactionFactory
from fetchai.ledger.serialisation import transaction
from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Address, Entity
from fetchai.ledger.transaction import Transaction
from .common import ApiEndpoint

EntityList = List[Entity]


class ContractsApi(ApiEndpoint):
    API_PREFIX = 'fetch.contract'

    def create(self, owner: Entity, contract: 'Contract', fee: int, signers: Optional[List[int]] = None,
               shard_mask: BitVector = None):
        ENDPOINT = 'create'

        logging.debug('Deploying contract', contract.address)

        tx = ContractTxFactory(self._parent_api).create(owner, contract, fee, shard_mask=shard_mask)

        # encode and sign the transaction
        # TODO: Is multisig contract creation possible?
        encoded_tx = transaction.encode_transaction(tx, signers if signers else [owner])

        # update the contracts owner
        contract.owner = owner

        # submit the transaction
        return self._post_tx_json(encoded_tx, ENDPOINT)

    def submit_data(self, entity: Entity, contract_address: Address, **kwargs):
        # build up the basic transaction information
        tx = Transaction()
        tx.from_address = Address(entity)
        tx.valid_until = 10000
        tx.target_contract(contract_address, BitVector())
        tx.charge_rate = 1
        tx.charge_limit = 1000000000000
        tx.action = 'data'
        tx.synergetic_data_submission = True
        tx.data = self._encode_json(dict(**kwargs))
        tx.add_signer(entity)

        # encode the transaction
        encoded_tx = transaction.encode_transaction(tx, [entity])

        # submit the transaction to the catch-all endpoint
        return self._post_tx_json(encoded_tx, None)

    def query(self, contract_owner: Address, query: str, **kwargs):
        return self._post_json(query, prefix=str(contract_owner), data=self._encode_json_payload(**kwargs))

    def action(self, contract_address: Address, action: str,
               fee: int, from_address: Address, *args,
               signers: EntityList, shard_mask: BitVector = None):

        tx = ContractTxFactory(self._parent_api).action(contract_address,
                                                        action, fee, from_address, *args,
                                                        signers=signers, shard_mask=shard_mask)
        tx.data = self._encode_msgpack_payload(*args)
        self._set_validity_period(tx)

        for signer in signers:
            tx.add_signer(signer)

        encoded_tx = transaction.encode_transaction(tx, signers)

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

    def _post_tx_json(self, tx_data: bytes, endpoint: Optional[str]):
        return super()._post_tx_json(tx_data=tx_data, endpoint=None)


class ContractTxFactory(TransactionFactory):
    API_PREFIX = 'fetch.contract'

    def __init__(self, api: 'LedgerApi'):
        self._api = api

    @property
    def server(self):
        """Replicate server interface for fetching number of lanes"""
        return self._api.server

    def _set_validity_period(self, tx: Transaction, validity_period: Optional[int] = None):
        """Replicate setting of validity period using server"""
        self._api.server._set_validity_period(tx, validity_period=validity_period)

    def action(self, contract_address: Address, action: str,
               fee: int, from_address: Address, *args,
               signers: Optional[List[Entity]] = None,
               shard_mask: Optional[BitVector] = None) -> Transaction:

        # Default to wildcard shard mask if none supplied
        if not shard_mask:
            logging.warning("Defaulting to wildcard shard mask as none supplied")
            shard_mask = BitVector()

        # build up the basic transaction information
        tx = self._create_action_tx(fee, from_address, action, shard_mask)
        tx.target_contract(contract_address, shard_mask)
        tx.data = self._encode_msgpack_payload(*args)
        self._set_validity_period(tx)

        if signers:
            for signer in signers:
                tx.add_signer(signer)
        else:
            tx.add_signer(from_address)

        return tx

    def create(self, owner: Entity, contract: 'Contract', fee: int, signers: Optional[List[Entity]] = None,
               shard_mask: Optional[BitVector] = None) -> Transaction:
        # Default to wildcard shard mask if none supplied
        if not shard_mask:
            logging.warning("Defaulting to wildcard shard mask as none supplied")
            shard_mask = BitVector()

        # build up the basic transaction information
        tx = self._create_action_tx(fee, owner, 'create', shard_mask)
        tx.data = self._encode_json({
            'nonce': contract.nonce,
            'text': contract.encoded_source,
            'digest': contract.digest.to_hex()
        })
        self._set_validity_period(tx)

        if signers:
            for signer in signers:
                tx.add_signer(signer)
        else:
            tx.add_signer(owner)

        return tx
