import unittest
from unittest.mock import patch

from fetchai.ledger.api import LedgerApi, ApiEndpoint


class BootstrapTests(unittest.TestCase):
    @patch('semver.match')
    @patch('fetchai.ledger.api.ApiEndpoint')
    @patch('fetchai.ledger.api.bootstrap.server_from_name')
    def test_called(self, mock_bootstrap, mock_api, mock_match):
        """Test that Api initialisation gets server details from bootstrap method"""
        # host/port details returned by bootstrap
        mock_bootstrap.side_effect = [('host', 1234)]
        # short-circuit version checking
        mock_match.side_effect = [True] * 2
        mock_api.version().side_effect = ['1.0.0']

        # Check that all four api's created are passed the network details
        with patch('fetchai.ledger.api.TokenApi') as tapi, \
            patch('fetchai.ledger.api.ContractsApi') as capi, \
            patch('fetchai.ledger.api.TransactionApi') as txapi, \
            patch('fetchai.ledger.api.ServerApi') as sapi:

            a = LedgerApi(network='alpha')

            tapi.assert_called_once_with('host', 1234)
            capi.assert_called_once_with('host', 1234)
            txapi.assert_called_once_with('host', 1234)
            sapi.assert_called_once_with('host', 1234)

        # Check that bootstrap is queried
        mock_bootstrap.assert_called_once_with('alpha')

    def test_hostport_or_network(self):
        """Tests that init accepts only a host+port pair, or a network"""
        # If providing host or port, must provide both
        with self.assertRaises(AssertionError):
            a = LedgerApi(host='host')
        with self.assertRaises(AssertionError):
            a = LedgerApi(port=1234)
        # If providing network, may not provide host or port
        with self.assertRaises(AssertionError):
            a = LedgerApi(host='host', network='alpha')
        with self.assertRaises(AssertionError):
            a = LedgerApi(port=1234, network='alpha')
        with self.assertRaises(AssertionError):
            a = LedgerApi(host='host', port=1234, network='alpha')

