# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

import requests
import semver

from fetchai.ledger import __version__, IncompatibleLedgerVersion


class NetworkUnavailableError(Exception):
    pass


def list_servers(active=True):
    """Gets list of (active) servers from bootstrap network"""
    params = {'active': 1} if active else {}
    servers_response = requests.get('https://bootstrap.fetch.ai/networks/', params=params)
    if servers_response.status_code != 200:
        raise requests.ConnectionError('Failed to get network status from bootstrap')

    return servers_response.json()


def is_server_valid(server_list, network):
    # Check requested server is on list
    available_servers = [s['name'] for s in server_list]
    if network not in available_servers:
        raise NetworkUnavailableError('Requested network not present on network: {}'.format(network))

    # Check network version
    server_details = next(s for s in server_list if s['name'] == network)
    if server_details['versions'] != '*':
        version_constraints = server_details['versions'].split(',')

        # Build required version (e.g.: 0.9.1-alpha2 -> 0.9.0)
        network_version_required = semver.parse(__version__)
        network_version_required['prerelease'] = None
        network_version_required['build'] = None
        network_version_required['patch'] = 0
        network_version_required = semver.format_version(**network_version_required)

        if not all(semver.match(network_version_required, c) for c in version_constraints):
            raise IncompatibleLedgerVersion("Requested network does not support required version\n" +
                                            "Required version: {}\nNetwork supports: {}".format(
                                                network_version_required, ', '.join(version_constraints)
                                            ))
    # Return true if server valid
    return True


def get_ledger_address(network):
    # Request server endpoints
    params = {'network': network}
    endpoints_response = requests.get('https://bootstrap.fetch.ai/endpoints', params=params)
    if endpoints_response.status_code != 200:
        raise requests.ConnectionError('Failed to get network endpoint from bootstrap')

    # Retrieve ledger endpoint
    ledger_endpoint = [s for s in endpoints_response.json() if s['component'] == 'ledger']
    if len(ledger_endpoint) != 1:
        raise NetworkUnavailableError('Requested server is not reporting a ledger endpoint')

    # Return server address
    ledger_endpoint = ledger_endpoint[0]
    if 'address' not in ledger_endpoint:
        raise RuntimeError('Ledger endpoint missing address')

    return ledger_endpoint['address']


def split_address(address):
    """Splits a url into a protocol, host name and port"""
    if '://' in address:
        protocol, address = address.split('://')
    else:
        protocol = 'http'

    if ':' in address:
        address, port = address.split(':')
    else:
        port = 443 if protocol == 'https' else 8000

    return protocol, address, int(port)


def server_from_name(network):
    """Queries bootstrap for the requested network and returns connection details"""

    # Adding a "local" network to give the looks and feel of main and testnet
    if network == "local":
        return "http://127.0.0.1", 8000

    # Get list of active servers
    server_list = list_servers(True)

    # Check requested network exists and supports our ledger version
    assert is_server_valid(server_list, network)

    # Get address of network ledger
    ledger_address = get_ledger_address(network)

    # Check if address contains a port
    protocol, host, port = split_address(ledger_address)

    return protocol + '://' + host, port
