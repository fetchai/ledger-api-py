import time

from fetch.ledger.api.wallet import WalletApi


class WalletApiExample(object):
    MAX_ITERATIONS = 20
    ITERATION_PERIOD_SECS = 0.5

    def __init__(self, host, port):
        self._api = WalletApi(host, port, 2)

    def _register(self):
        address = self._api.register()

        if address is None:
            raise RuntimeError('Unable to request address from wallet API')

        # wait for a positive balance to be created (sort of backed into the contract)
        balance = 0
        for n in range(self.MAX_ITERATIONS):
            balance = self._balance(address)
            if balance > 0:
                break

            time.sleep(self.ITERATION_PERIOD_SECS)

        if balance == 0:
            raise RuntimeError('Failed to generate a balance from the registered account: ' + address)

        return address

    def _create_accounts(self, count):

        raw_data = self._api.register(count)
        accounts = self._api.to_accounts(raw_data)

        if accounts is None:
            raise RuntimeError('Unable to create accounts from wallet API')

        # don't wait for the balances to show, verify this later
        return accounts

    def _balance(self, address):
        if address is None:
            return False

        # wait for a balance to be presented
        balance = None
        for n in range(self.MAX_ITERATIONS):
            balance = self._api.balance(address)

            # exit the loop if the balance has been retrieved
            if balance is not None:
                break

            # wait for the data to become available
            time.sleep(self.ITERATION_PERIOD_SECS)

        if balance is None:
            raise RuntimeError('Unable to request balance for address: ')

        return balance

    def _transfer(self, from_address, to_address, amount):
        if not self._api.transfer(from_address, to_address, amount):
            raise RuntimeError('Failed to submit the transfer transaction')

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


class MultipleBalanceRequest(WalletApiExample):
    def run(self, count = 100):

        # register with the ledger for addresses
        self.accounts = self._create_accounts(count)
