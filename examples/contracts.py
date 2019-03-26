contract_source = """

    @init
    function initialize(owner: Address)
        var INITIAL_SUPPLY = 100000000000ul;

        var account = State<UInt64>(owner, 0ul);
        account.set(INITIAL_SUPPLY);
    endfunction

    @action
    function transfer(from: Address, to: Address, amount: UInt64)

      // define the accounts
      var from_account = State<UInt64>(from, 0ul);
      var to_account = State<UInt64>(to, 0ul); // if new sets to 0u

      // Check if the sender has enough balance to proceed
      if (from_account.get() >= amount)
        from_account.set(from_account.get() - amount);
        to_account.set(to_account.get() + amount);
      endif

    endfunction

    @query
    function balance(address: Address) : UInt64
        var account = State<UInt64>(address, 0ul);
        return account.get();
    endfunction

"""

import base64
import time
import hashlib
import json
import binascii
import msgpack

from fetchai.ledger.serialisation.objects.transaction_api import create_json_tx
from fetchai.ledger.api import ContractsApi, TransactionApi, submit_json_transaction
from fetchai.ledger.crypto import Identity

HOST = '127.0.0.1'
PORT = 8000


identity = Identity()
next_identity = Identity()

status_api = TransactionApi(HOST, PORT)
contract_api = ContractsApi(HOST, PORT)

create_tx = contract_api.create(identity, contract_source, init_resources = ["owner", identity.public_key])

print('CreateTX:', create_tx)

while True:
    status = status_api.status(create_tx)

    print(status)
    if status == "Executed":
        break

    time.sleep(1)

# re-calc the digest
hash_func = hashlib.sha256()
hash_func.update(contract_source.encode())
source_digest = base64.b64encode(hash_func.digest()).decode()

print('transfer N times')

for index in range(3):

    # create the tx
    tx = create_json_tx(
        contract_name=source_digest + '.' + identity.public_key + '.transfer',
        json_data=msgpack.packb([msgpack.ExtType(77, identity.public_key_bytes), msgpack.ExtType(77, next_identity.public_key_bytes), 1000 + index]),
        resources=['owner', identity.public_key, next_identity.public_key],
        raw_resources=[source_digest],
    )

    # sign the transaction contents
    tx.sign(identity.signing_key)

    wire_fmt = json.loads(tx.to_wire_format())
    # print(wire_fmt)

    # # submit that transaction
    code = submit_json_transaction(HOST, PORT, wire_fmt)

    print('Submitted TX:', code)

    time.sleep(5)

print('Query for owner funds')

source_digest_hex = binascii.hexlify(base64.b64decode(source_digest)).decode()

url = 'http://{}:{}/api/contract/{}/{}/balance'.format(HOST, PORT, source_digest_hex, identity.public_key_hex)

print(url)

r = status_api._session.post(url, json={
    'address': identity.public_key
})
print(r.status_code)
print(r.json())
