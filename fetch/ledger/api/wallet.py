from .common import ApiEndpoint


class WalletApi(ApiEndpoint):
    @property
    def api_prefix(self):
        api_version = self.api_version
        assert api_version in (1, 2)

        if api_version == 1:
            return '/'
        elif api_version == 2:
            return '/api/wallet/'
        else:
            assert False

    def register(self):
        success, data = self._post(self.api_prefix + 'register')
        if success and 'address' in data:
            return data['address']

    def balance(self, address):
        request = {
            'address': address
        }
        success, data = self._post(self.api_prefix + 'balance', request)
        if success and 'balance' in data:
            return data['balance']

    def transfer(self, from_address, to_address, amount):
        request = {
            'from': from_address,
            'to': to_address,
            'amount': amount
        }
        success, _ = self._post(self.api_prefix + 'transfer', request)
        if success:
            return True
