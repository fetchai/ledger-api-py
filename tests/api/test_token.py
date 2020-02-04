from typing import Callable
from unittest import TestCase
from unittest.mock import patch, MagicMock

from fetchai.ledger.api import TokenApi
from fetchai.ledger.api.token import TokenTxFactory
from fetchai.ledger.crypto import Address, Entity
from fetchai.ledger.crypto.deed import Deed
from fetchai.ledger.transaction import Transaction


class TokenAPITests(TestCase):
    def setUp(self) -> None:
        self.entity = Entity()
        self.address = Address(self.entity)
        self.to_address = Address(Entity())

        with patch('requests.session') as mock_session:
            self.api = TokenApi('127.0.0.1', 8000)

    def query_test(self, function, action: str):
        with patch('fetchai.ledger.api.TokenApi._post_json') as mock_post, \
                patch('warnings.warn') as mock_warn:
            mock_post.side_effect = [(True, {action: 200})]

            result = function(self.address)

            mock_post.assert_called_once_with(action, {'address': str(self.address)})

            self.assertEqual(result, 200)

    def test_balance(self):
        self.query_test(self.api.balance, 'balance')

    def test_stake(self):
        self.query_test(self.api.stake, 'stake')

    def post_test(self, function: Callable, action: str, factory_function: Callable, entity: Entity, *args):
        with patch('fetchai.ledger.api.TokenApi._post_tx_json') as mock_post, \
                patch('fetchai.ledger.api.token.TokenTxFactory.' + factory_function.__name__,
                      autospec=factory_function) as mock_factory, \
                patch('fetchai.ledger.api.TokenApi._set_validity_period') as mock_set_valid, \
                patch('warnings.warn') as mock_warnings, \
                patch('fetchai.ledger.serialisation.transaction.encode_transaction') as mock_encode:
            # the transaction factory should generate a known transaction
            tx = Transaction()
            tx.sign = MagicMock()
            tx.sign.side_effect = [None]
            mock_factory.side_effect = [tx]

            mock_post.side_effect = ['result']
            mock_encode.side_effect = ['encoded']

            # run the production code
            result = function(entity, *args)

            mock_factory.assert_called_once_with(entity, *args, [entity])
            mock_set_valid.assert_called_once_with(tx)
            tx.sign.assert_called_once_with(entity)
            mock_encode.assert_called_once_with(tx)
            mock_post.assert_called_once_with('encoded', action)
            self.assertEqual(result, 'result')

    def test_deed(self):
        self.post_test(self.api.deed, 'deed', TokenTxFactory.deed, self.entity, Deed(), 2000)

    def test_transfer(self):
        self.post_test(self.api.transfer, 'transfer', TokenTxFactory.transfer,
                       self.entity, self.to_address, 500, 500)

    def test_add_stake(self):
        self.post_test(self.api.add_stake, 'addStake', TokenTxFactory.add_stake,
                       self.entity, 500, 500)

    def test_de_stake(self):
        self.post_test(self.api.de_stake, 'deStake', TokenTxFactory.de_stake,
                       self.entity, 500, 500)

    def test_collect_stake(self):
        self.post_test(self.api.collect_stake, 'collectStake', TokenTxFactory.collect_stake,
                       self.entity, 500)
