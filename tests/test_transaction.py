from unittest import TestCase
from unittest.mock import patch

from fetchai.ledger.bitvector import BitVector

from fetchai.ledger.crypto import Identity, Address

from fetchai.ledger.crypto import Entity
from fetchai.ledger.api.token import TokenTxFactory
from fetchai.ledger.transaction import Transaction


class TransactionTests(TestCase):
    def setUp(self) -> None:
        self.source_identity = Entity()
        self.multi_sig_identity = Entity()
        self.multi_sig_board = [Entity() for _ in range(4)]
        self.target_identity = Entity()

        self.tx = TokenTxFactory.transfer(self.source_identity, Identity(self.target_identity),
                                          500, 500, [self.source_identity])
        self.mstx = TokenTxFactory.transfer(self.multi_sig_identity, Identity(self.target_identity),
                                          500, 500, self.multi_sig_board)

    def test_partial_serialize(self):
        self.mstx.sign(self.multi_sig_board[0])
        self.mstx.sign(self.multi_sig_board[2])

        encoded = self.mstx.encode_partial()

        tx2 = Transaction.decode_partial(encoded)

        self.assertTrue(self.mstx.compare(tx2))

        # Check that signer signatures match that sent
        for signer in self.mstx.signers:
            self.assertIn(signer, tx2.signers)
            if self.mstx.signers[signer] == {}:
                self.assertEqual(tx2.signers[signer], {})
            else:
                self.assertEqual(self.mstx.signers[signer]['signature'], tx2.signers[signer]['signature'])
                self.assertEqual(self.mstx.signers[signer]['verified'], tx2.signers[signer]['verified'])

    def test_invalid_sig(self):
        self.mstx.sign(self.multi_sig_board[0])
        self.mstx.signers[self.multi_sig_board[0]]['signature'] = b'invalid'

        encoded = self.mstx.encode_partial()

        with patch('logging.warning') as mock_warn:
            tx2 = Transaction.decode_partial(encoded)
            self.assertEqual(mock_warn.call_count, 1)

        self.assertFalse(tx2.signers[self.multi_sig_board[0]]['verified'])

    def test_merge_tx_signatures(self):
        payload = self.mstx.payload

        txs = []
        for signer in self.multi_sig_board:
            tx = Transaction.from_payload(payload)
            tx.sign(signer)
            txs.append(tx.encode_partial())

        for tx in txs:
            self.mstx.merge_signatures(Transaction.decode_partial(tx))

        self.assertTrue(all([s['verified'] for s in self.mstx.signers.values()]))

    def test_payload(self):
        payload = self.tx.payload
        new_tx = Transaction.from_payload(payload)
        self.assertTrue(new_tx.compare(self.tx))

    def test_compare(self):
        tx = TokenTxFactory.transfer(self.source_identity, Identity(self.target_identity),
                                     500, 500, [self.source_identity])
        payload = tx.payload
        tx2 = Transaction.from_payload(payload)

        self.assertTrue(tx.compare(tx2))

        # Test comparison fails if any data changed
        tx2 = Transaction.from_payload(payload)
        tx2.from_address = Entity()
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2.add_transfer(Entity(), 500)
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2.valid_from = 999
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2.valid_until = 999
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2.charge_rate = 999
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2.charge_limit = 999
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2._contract_digest = Address(Entity())
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2._contract_address = Address(Entity())
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2._chain_code = 'changed'
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2._action = 'changed'
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2._shard_mask = BitVector(size=16)
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2.data = b'changed'
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2.add_signer(Entity())
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2._counter = 999
        self.assertFalse(tx.compare(tx2))

        tx2 = Transaction.from_payload(payload)
        tx2._metadata['new'] = True
        self.assertFalse(tx.compare(tx2))

