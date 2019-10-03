import semver

# Ledger version that this API is compatible with
__version__ = '0.9.0-a1'
# This API is compatible with ledgers that meet all the requirements listed here:
__compatible__ = ['<0.10.0', '>=0.8.0-alpha']
# Require ledger network to support this version: TODO: standardise how this version is selected
__network_required__ = '0.8.0'


class IncompatibleLedgerVersion(Exception):
    pass
