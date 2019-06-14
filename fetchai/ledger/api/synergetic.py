from .common import ApiEndpoint
from fetchai.ledger.transaction import Transaction
from fetchai.ledger.crypto import Address, Entity
from fetchai.ledger.serialisation import encode_transaction


class SynergeticApi(ApiEndpoint):
    def submit_data(self, entity: Entity, digest: Address, **kwargs):

        # build up the basic transaction information
        tx = Transaction()
        tx.from_address = Address(entity)
        tx.valid_until = 10000
        tx.target_synergetic(digest)
        tx.charge_rate = 1
        tx.charge_limit = 1
        tx.action = 'data'
        tx.data = self._encode_json(dict(**kwargs))
        tx.add_signer(entity)

        # encode the transaction
        encoded_tx = encode_transaction(tx, [entity])

        # submit the transaction to the catch all endpoint
        return self._post_tx_json(encoded_tx, None)

