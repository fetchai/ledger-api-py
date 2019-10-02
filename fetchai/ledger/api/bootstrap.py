import requests

class NetworKUnavailableError(Exception)

def server_from_name(network):
    # Get list of active servers
    params = {'active': 1}
    servers_response = requests.get('https://bootstrap.fetch.ai/networks/', params=params)
    if servers_response.status_code != 200:
        raise requests.ConnectionError('Failed to get network status from bootstrap')

    # Check requested server is on list
    available_servers = [s['name'] for s in servers_response.json()]
    if network not in available_servers:
        raise NetworKUnavailableError('Requested network not present on network: {}'.format(network))

    # Check network version
    server_version = next(s for s in servers_response.json() if s['name'] == network)['versions']
    # TODO: Not sure how to compare this string to our requirements

    # Request server endpoints
    params = {'network': network}
    endpoints_response = requests.get('https://bootstrap.fetch.ai/endpoints', params=params)
    if servers_response.status_code != 200:
        raise requests.ConnectionError('Failed to get network endpoint from bootstrap')

    # Retrieve ledger endpoint
    ledger_endpoint = [s for s in endpoints_response.json() if s['component'] == 'ledger']
    if len(ledger_endpoint) != 1:
        raise NetworKUnavailableError('Requested server is not reporting a ledger endpoint')

    # Return server address
    ledger_endpoint = ledger_endpoint[0]
    if 'address' not in ledger_endpoint:
        raise RuntimeError('Ledger endpoint missing address')

    # Return address and port
    ledger_address = ledger_endpoint['address']

    # Check if address contains a port
    address = ledger_address.split('://')[-1] if '://' in ledger_address else ledger_address
    if ':' in address:
        address, port = address.split(':')
        return address, int(port)
    else:
        # If no port specified, default to 443
        # TODO: Sensible default for http?
        return ledger_address, 443



