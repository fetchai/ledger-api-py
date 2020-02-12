# Ledger version that this API is compatible with
__version__ = '1.0.2'
# This API is compatible with ledgers that meet all the requirements listed here:
__compatible__ = ['>=0.11.0-alpha.7']


class IncompatibleLedgerVersion(Exception):
    pass
