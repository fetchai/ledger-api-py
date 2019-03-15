import base64
import hashlib

from fetchai.ledger.serialisation.objects.transaction_api import create_json_tx
from .common import ApiEndpoint


class ContractsApi(ApiEndpoint):
    API_PREFIX = 'fetch.contract'

    def create(self, identity, source, init_resources = []):
        source = source.encode()

        hash_func = hashlib.sha256()
        hash_func.update(source)

        source_digest = base64.b64encode(hash_func.digest()).decode()

        data = {
            'text': base64.b64encode(source).decode(),
            'digest': source_digest,
        }

        # Need to construct the raw resources needed for SC creation init.
        init_resources_appended = [source_digest+"."+identity.public_key+".state."+x for x in init_resources]

        # create the tx
        tx = create_json_tx(
            contract_name=self.API_PREFIX + '.create',
            json_data=data,
            resources=[source_digest],
            raw_resources=[source_digest, *init_resources_appended],
        )

        # sign the transaction contents
        tx.sign(identity.signing_key)

        return self._post_tx(tx.to_wire_format(), 'create')
