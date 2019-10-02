import requests


def server_from_name(server_name):
    # Get list of active servers
    servers_response = requests.get('https://bootstrap.fetch.ai/networks/')
    assert servers_response.status_code == 200, 'Failed to get network status'

    # Check requested server is on list
    available_servers = [s['name'] for s in servers_response.json()]
    assert server_name in available_servers, 'Requested server not present on network: {}'.format(server_name)

    # Request server endpoints
    endpoints_response = requests.get('https://bootstrap.fetch.ai/endpoints', params={'network': server_name})
    assert endpoints_response.status_code == 200, 'Failed to get server status'

    # Retrieve ledger endpoint
    ledger_endpoint = [s for s in endpoints_response.json() if s['component'] == 'ledger']
    assert len(ledger_endpoint) == 1, 'Requested server is not reporting a ledger endpoint'

    # Return server address
    ledger_endpoint = ledger_endpoint[0]
    assert 'address' in ledger_endpoint, 'Ledger endpoint missing address'

    # Return address and port
    ledger_address = ledger_endpoint['address']
    # if ':' in ledger_address:
    #     address, port = ledger_address.split(':')
    #     return address, int(port)
    # else:
    return ledger_address, 443




