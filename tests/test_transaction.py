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
        self.mstx.sign2(self.multi_sig_board[0])
        self.mstx.sign2(self.multi_sig_board[2])
        self.assertEqual(len(self.mstx.present_signers), 2)

        encoded = self.mstx.encode_partial2()

        success, tx2 = Transaction.decode_partial2(encoded)

        self.assertFalse(success) # not all the signatures are populated
        self.assertEqual(self.mstx, tx2) # the body of the payload should be the same
        self.assertEqual(list(self.mstx.signatures), list(tx2.signatures)) # the signature present should all be the same
        self.assertEqual(len(tx2.present_signers), 2)

    def test_invalid_sig(self):
        self.mstx.add_signature(self.multi_sig_board[0], b'invalid')

        encoded = self.mstx.encode_partial2()

        success, tx2 = Transaction.decode_partial2(encoded)
        self.assertFalse(success)
        self.assertFalse(tx2.is_valid())

    def test_merge_tx_signatures(self):
        payload = self.mstx.encode_payload()

        partials = []
        for signer in self.multi_sig_board:
            tx = Transaction.decode_payload(payload)
            tx.sign2(signer)
            partials.append(tx.encode_partial2())

        for partial in partials:
            _, partial_tx = Transaction.decode_partial2(partial)
            self.assertTrue(self.mstx.merge_signatures(partial_tx))

        self.assertTrue(self.mstx.is_valid())

    def test_payload(self):
        payload = self.tx.encode_payload()
        new_tx = Transaction.decode_payload(payload)
        self.assertEqual(new_tx, self.tx)

    def test_compare(self):
        tx = TokenTxFactory.transfer(self.source_identity, Identity(self.target_identity),
                                     500, 500, [self.source_identity])

        # encode the transaction so that copies can be made afterwards
        encoded_tx = tx.encode_partial2()

        # Test comparison fails if any data changed
        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2.from_address = Entity()
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2.add_transfer(Entity(), 500)
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2.valid_from = 999
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2.valid_until = 999
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2.charge_rate = 999
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2.charge_limit = 999
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2._contract_address = Address(Entity())
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2._chain_code = 'changed'
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2._action = 'changed'
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2._shard_mask = BitVector(size=16)
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2.data = b'changed'
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2.add_signer(Entity())
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2._counter = 999
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial2(encoded_tx)
        tx2._metadata['new'] = True
        self.assertNotEqual(tx, tx2)

    def test_from_encoded(self):
        new_tx = Transaction.decode_payload(self.tx.encode_payload())
        self.assertEqual(self.tx, new_tx)