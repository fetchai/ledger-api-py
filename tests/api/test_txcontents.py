from unittest import TestCase
from unittest.mock import Mock, patch

import requests

from fetchai.ledger.api import TransactionApi
from fetchai.ledger.api.tx import TxContents
from fetchai.ledger.crypto import Address, Identity, Entity


class TXContentsTest(TestCase):
    def test_init(self):
        pass

    @patch('fetchai.ledger.api.tx.TxContents', spec=TxContents)
    def test_contents(self, mock_contents):
        """Check that transcation api correctly queries for and returns contents"""
        # Api object
        api = TransactionApi('abc', 1234)

        # Sessions mock for receiving URL request
        mock_session = Mock(spec=requests.Session)
        api._session = mock_session

        # Mock response returned by session
        mock_response = Mock(spec=requests.Response)
        mock_response.json.side_effect = ['json']
        mock_session.get.side_effect = [mock_response]

        # Mock TxContents static constructor
        mock_contents.from_json.side_effect = ['txcontents']

        # Call method under test
        result = api.contents('fegh')

        # Check that correct url retrieved
        mock_session.get.assert_called_once_with('http://abc:1234/api/tx/fegh')
        # Check that json result retrieved
        mock_response.json.assert_called_once_with()
        # Check that static constructor called
        mock_contents.from_json.assert_called_once_with('json')
        # Check that correct result returned
        self.assertEqual(result, 'txcontents')

    def test_static_constructor(self):
        data = {
            'digest': '0x123456',
            'action': 'transfer',
            'chainCode': 'action.transfer',
            'from': 'U5dUjGzmAnajivcn4i9K4HpKvoTvBrDkna1zePXcwjdwbz1yB',
            'validFrom': 0,
            'validUntil': 100,
            'charge': 2,
            'chargeLimit': 5,
            'transfers': [],
            'signatories': ['abc'],
            'data': 'def'
        }

        a = TxContents.from_json(data)
        self.assertEqual(a._digest_bytes, bytes.fromhex('123456'))
        self.assertEqual(a._digest_hex, '123456')
        self.assertEqual(a.action, 'transfer')
        self.assertEqual(a.chain_code, 'action.transfer')
        self.assertEqual(a.from_address, Address('U5dUjGzmAnajivcn4i9K4HpKvoTvBrDkna1zePXcwjdwbz1yB'))
        self.assertIsNone(a.contract_digest)
        self.assertIsNone(a.contract_address)
        self.assertEqual(a.valid_from, 0)
        self.assertEqual(a.valid_until, 100)
        self.assertEqual(a.charge, 2)
        self.assertEqual(a.charge_limit, 5)
        self.assertEqual(a.transfers, {})
        self.assertEqual(a.data, 'def')

    def test_transfers(self):
        to1 = Entity()
        to2 = Entity()
        to3 = Entity()

        data = {
            'digest': '0x123456',
            'action': 'transfer',
            'chainCode': 'action.transfer',
            'from': 'U5dUjGzmAnajivcn4i9K4HpKvoTvBrDkna1zePXcwjdwbz1yB',
            'validFrom': 0,
            'validUntil': 100,
            'charge': 2,
            'chargeLimit': 5,
            'signatories': ['abc'],
            'data': 'def',
            'transfers': [
                {'to': to1, 'amount': 200},
                {'to': to2, 'amount': 300}
            ]
        }

        a = TxContents.from_json(data)

        self.assertEqual(a.transfers_to(to1), 200)
        self.assertEqual(a.transfers_to(to2), 300)
        self.assertEqual(a.transfers_to(to3), 0)
