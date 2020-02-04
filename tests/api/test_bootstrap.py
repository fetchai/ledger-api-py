import unittest
from unittest.mock import patch, Mock

import requests

from fetchai.ledger import IncompatibleLedgerVersion
from fetchai.ledger.api import LedgerApi
from fetchai.ledger.api.bootstrap import list_servers, NetworkUnavailableError, is_server_valid, get_ledger_address, \
    split_address, server_from_name


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
            _ = LedgerApi(network='alpha')

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

    @patch('requests.get')
    def test_list_servers(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.side_effect = [mock_response]

        # Test get called as expected
        list_servers(True)
        mock_response.json.assert_called_once_with()
        mock_get.assert_called_once_with('https://bootstrap.fetch.ai/networks/', params={'active': 1})

        # Test correct call when not filtering for activity
        mock_response.json.reset_mock()
        mock_get.reset_mock()
        mock_get.side_effect = [mock_response]
        list_servers(False)
        mock_response.json.assert_called_once_with()
        mock_get.assert_called_once_with('https://bootstrap.fetch.ai/networks/', params={})

        # Test exception thrown on connection error
        mock_response.status_code = 404
        mock_get.reset_mock()
        mock_get.side_effect = [mock_response]
        with self.assertRaises(requests.exceptions.ConnectionError):
            list_servers()

    @patch('semver.match')
    def test_is_server_valid(self, mock_match):
        # Test error thrown if server not on list
        server_list = [{'name': n} for n in ['abc', 'def', 'hij']]
        network = 'xyz'
        with self.assertRaises(NetworkUnavailableError):
            is_server_valid(server_list, network)

        # Test error thrown if versions incompatible
        server_list = [{'name': n, 'versions': '>=0.6.0,<0.7.0'} for n in ['abc', 'def', 'hij']]
        network = 'def'
        mock_match.side_effect = [True, False]
        with self.assertRaises(IncompatibleLedgerVersion):
            is_server_valid(server_list, network)

        # Test True returned if tests pass
        server_list = [{'name': n, 'versions': '>=0.6.0,<0.7.0'} for n in ['abc', 'def', 'hij']]
        network = 'def'
        mock_match.side_effect = [True, True]
        try:
            out = is_server_valid(server_list, network)
            self.assertTrue(out)
        except Exception:
            self.fail()

    @patch('requests.get')
    def test_get_ledger_address(self, mock_get):
        network = 'def'
        # Test Connection error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.side_effect = [mock_response]
        with self.assertRaises(requests.exceptions.ConnectionError):
            get_ledger_address(network)

        # Test failure if ledger missing
        mock_response.status_code = 200
        mock_response.json.side_effect = [[{'network': network, 'component': c, 'address': 'https://foo.bar:500'}
                                           for c in ['oef-core', 'oef-ms']]]
        mock_get.side_effect = [mock_response]
        with self.assertRaises(NetworkUnavailableError):
            get_ledger_address(network)

        # Test failure on address missing
        mock_response.json.side_effect = [[{'network': network, 'component': c}
                                           for c in ['oef-core', 'oef-ms', 'ledger']]]
        mock_get.side_effect = [mock_response]
        with self.assertRaises(RuntimeError):
            get_ledger_address(network)

        # Test correct return of address
        mock_response.status_code = 200
        mock_response.json.side_effect = [[{'network': network, 'component': c, 'address': 'https://foo.bar:500'}
                                           for c in ['oef-core', 'oef-ms', 'ledger']]]
        mock_get.side_effect = [mock_response]
        out = get_ledger_address(network)
        self.assertEqual(out, 'https://foo.bar:500')

    def test_split_address(self):
        # Test correct splitting of address into protocol, host, port
        protocol, host, port = split_address('https://foo.bar:500')
        self.assertEqual(protocol, 'https')
        self.assertEqual(host, 'foo.bar')
        self.assertEqual(port, 500)

        # Test defaulting of protocol to http
        protocol, host, port = split_address('foo.bar:500')
        self.assertEqual(protocol, 'http')
        self.assertEqual(host, 'foo.bar')
        self.assertEqual(port, 500)

        # Test default ports depending on protocol
        protocol, host, port = split_address('https://foo.bar')
        self.assertEqual(protocol, 'https')
        self.assertEqual(host, 'foo.bar')
        self.assertEqual(port, 443)

        protocol, host, port = split_address('http://foo.bar')
        self.assertEqual(protocol, 'http')
        self.assertEqual(host, 'foo.bar')
        self.assertEqual(port, 8000)

    @patch('fetchai.ledger.api.bootstrap.list_servers')
    @patch('fetchai.ledger.api.bootstrap.is_server_valid')
    @patch('fetchai.ledger.api.bootstrap.get_ledger_address')
    @patch('fetchai.ledger.api.bootstrap.split_address')
    def test_server_from_name(self, mock_split, mock_address, mock_valid, mock_servers):
        # Test that all steps called with expected arguments
        network = 'def'
        mock_servers.side_effect = ['servers']
        mock_valid.side_effect = [True]
        mock_address.side_effect = ['address']
        mock_split.side_effect = [('protocol', 'host', 1234)]

        host, port = server_from_name(network)

        mock_servers.assert_called_once_with(True)
        mock_valid.assert_called_once_with('servers', network)
        mock_address.assert_called_once_with(network)
        mock_split.assert_called_once_with('address')

        self.assertEqual(host, 'protocol://host')
        self.assertEqual(port, 1234)
