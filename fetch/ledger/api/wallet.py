from .common import ApiEndpoint
import time

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

    def register(self, count=1):

        if(count == 1):
            # Old style registering
            success, data = self._post(self.api_prefix + 'register')
            if success and 'address' in data:
                return data['address']
        else:
            # New style bulk registering
            request = {
                'count': count
            }

            success, data = self._post(self.api_prefix + 'register', request)

            if "addresses" not in data:
                raise RuntimeError('Failed to parse JSON when registering: ' + str(data))

            return data["addresses"]

    def to_accounts(self, addresses):
        return [Account(self, x) for x in addresses]

    def balance(self, address):
        request = {
            'address': address
        }
        success, data = self._post(self.api_prefix + 'balance', request)

        if success and 'balance' in data:
            return data['balance']
        else:
            raise RuntimeError('Failed to find a balance at address: ' + address)

    def transfer(self, from_address, to_address, amount):
        request = {
            'from': from_address,
            'to': to_address,
            'amount': amount
        }
        success, _ = self._post(self.api_prefix + 'transfer', request)
        if success:
            return True

# Account class for managing accounts easily
class Account():
    MAX_ITERATIONS        = 300
    ITERATION_PERIOD_SECS = 0.5

    def __init__(self, api, address):
        self._api     = api
        self._address = address
        self._balance = 0

    # For now, we assume that if we are updating that the balance must have changed
    def update(self, expect_new_balance=True):

        for i in range(self.MAX_ITERATIONS):
            new_balance = self._api.balance(self._address)
            if(self._balance != new_balance or not expect_new_balance):
                self._balance = new_balance
                return
            time.sleep(self.ITERATION_PERIOD_SECS)
        else:
            raise RuntimeError('Failed to get new balance at: {} . Old balance: {} '.format(self._address, self._balance))

    @property
    def address(self):
        return self._address

    @property
    def balance(self):
        return self._balance

    def send_funds(self, amount, other):
        other_address = other.address

        self._api.transfer(self.address, other_address, amount)

        if(amount != 0):
            self.update()
            other.update()
    @property
    def abbrev_address(self):
        return self._address[0:15]

    def __str__(self):
        return "Account {} Balance {}".format(self.abbrev_address, self._balance)

    def __repr__(self):
        return "Account {} Balance {}".format(self._address, self._balance)

