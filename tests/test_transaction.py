from unittest import TestCase

from fetchai.ledger.api.token import TokenTxFactory
from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Entity
from fetchai.ledger.crypto import Identity, Address
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
        self.assertEqual(len(self.mstx.present_signers), 2)

        encoded = self.mstx.encode_partial()

        success, tx2 = Transaction.decode_partial(encoded)

        self.assertFalse(success)  # not all the signatures are populated
        self.assertEqual(self.mstx, tx2)  # the body of the payload should be the same
        self.assertEqual(list(self.mstx.signatures),
                         list(tx2.signatures))  # the signature present should all be the same
        self.assertEqual(len(tx2.present_signers), 2)

    def test_invalid_sig(self):
        self.mstx.add_signature(self.multi_sig_board[0], b'invalid')

        encoded = self.mstx.encode_partial()

        success, tx2 = Transaction.decode_partial(encoded)
        self.assertFalse(success)
        self.assertFalse(tx2.is_valid())

    def test_merge_tx_signatures(self):
        payload = self.mstx.encode_payload()

        partials = []
        for signer in self.multi_sig_board:
            tx = Transaction.decode_payload(payload)
            tx.sign(signer)
            partials.append(tx.encode_partial())

        for partial in partials:
            _, partial_tx = Transaction.decode_partial(partial)
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
        encoded_tx = tx.encode_partial()

        # Test comparison fails if any data changed
        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2.from_address = Entity()
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2.add_transfer(Entity(), 500)
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2.valid_from = 999
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2.valid_until = 999
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2.charge_rate = 999
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2.charge_limit = 999
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2._contract_address = Address(Entity())
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2._chain_code = 'changed'
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2._action = 'changed'
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2._shard_mask = BitVector(size=16)
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2.data = b'changed'
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2.add_signer(Entity())
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2._counter = 999
        self.assertNotEqual(tx, tx2)

        _, tx2 = Transaction.decode_partial(encoded_tx)
        tx2._is_synergetic = True
        self.assertNotEqual(tx, tx2)

    def test_from_encoded(self):
        new_tx = Transaction.decode_payload(self.tx.encode_payload())
        self.assertEqual(self.tx, new_tx)

    def test_equal_to_invalid_type(self):
        self.assertNotEqual(self.tx, 5000324234)

    def test_add_signature_for_non_signer(self):
        with self.assertRaises(RuntimeError):
            self.tx.add_signature(Entity(), bytes())

    def test_merge_fail_on_different_tx(self):
        self.assertFalse(self.tx.merge_signatures(self.mstx))

    def test_merge_fail_on_no_signatures(self):
        entity = Entity()

        ref = Transaction()
        ref.counter = 0
        ref.add_signer(entity)
        ref.from_address = entity
        other = Transaction()
        other.counter = 0
        other.add_signer(entity)
        other.from_address = entity

        self.assertFalse(ref.merge_signatures(other))

    def test_handling_of_invalid_signatures(self):
        entity = Entity()

        ref = Transaction()
        ref.counter = 0
        ref.add_signer(entity)
        ref.from_address = entity
        other = Transaction()
        other.counter = 0
        other.add_signer(entity)
        other.from_address = entity
        other.add_signature(entity, b'clearly invalid sig')

        self.assertFalse(ref.merge_signatures(other))

    def test_encoding_of_tx_when_incomplete(self):
        self.assertTrue(self.tx.is_incomplete)
        self.assertIsNone(self.tx.encode())

    def test_encoding_of_complete_tx(self):
        self.tx.sign(self.source_identity)
        self.assertFalse(self.tx.is_incomplete)

        encoded = self.tx.encode()
        recovered_tx = Transaction.decode(encoded)
        self.assertIsNotNone(recovered_tx)
        self.assertEqual(self.tx, recovered_tx)

    def test_failure_to_decode_partial(self):
        encoded_partial = self.tx.encode_partial()

        self.assertIsNone(Transaction.decode(encoded_partial))
