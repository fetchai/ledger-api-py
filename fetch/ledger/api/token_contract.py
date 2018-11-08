from fetch.ledger.api import ApiEndpoint
from fetch.ledger.chain.transaction_api import create_wealth_tx, create_transfer_tx
from fetch.ledger.crypto.signing import Signing

import time

class TokenContractApi(ApiEndpoint):
    @property
    def api_prefix(self):
        api_version = self.api_version
        return '/api/contract/'

    def wealth(self, private_key_bin, amount, fee=0):
        priv_key = Signing.privKeyFromBin(private_key_bin)
        tx = create_wealth_tx(priv_key.get_verifying_key().to_string(), amount, fee)
        tx.sign(priv_key)
        wire_tx = tx.toWireFormat()
        return self.submit(wire_tx)

    def transfer(self, private_key_bin, to_address, amount, fee=0):
        priv_key = Signing.privKeyFromBin(private_key_bin)
        tx = create_transfer_tx(priv_key.get_verifying_key().to_string(), to_address, amount, fee=fee)
        tx.sign(priv_key)
        wire_tx = tx.toWireFormat()
        return self.submit(wire_tx)

    def submit(self, wire_tx):
        success, _ = self._post(self.api_prefix + 'submit', wire_tx)
        if success:
            return True

