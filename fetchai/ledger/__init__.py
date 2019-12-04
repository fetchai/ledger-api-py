# Ledger version that this API is compatible with
__version__ = '0.10.2'
# This API is compatible with ledgers that meet all the requirements listed here:
__compatible__ = ['<0.12.0-0', '>=0.10.1-0']


class IncompatibleLedgerVersion(Exception):
    pass
