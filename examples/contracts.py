import base64
import time
import hashlib
import json
import binascii

from fetchai.ledger.serialisation.objects.transaction_api import create_json_tx
from fetchai.ledger.api import ContractsApi, TransactionApi, submit_json_transaction
from fetchai.ledger.crypto import Identity

HOST = '127.0.0.1'
PORT = 8000

contract_source = """
@on_init
function on_init()
  var state = State<Int32>("value", 9);
  state.set(state.get());
  Print("on_init triggered, setting to: " + toString(state.get()));

  var other_state = State<Int32>("value", 33);
  Print("we see:" + toString(other_state.get()));
endfunction

@action
function increment()
  var state = State<Int32>("value", 10);
  state.set(state.get() + 3000);
endfunction

@query
function value() : Int32
  var state = State<Int32>("value", 12);
  Print("query triggered. State: "+ toString(state.get()));
  return state.get();
endfunction

"""

identity = Identity()

status_api = TransactionApi(HOST, PORT)
contract_api = ContractsApi(HOST, PORT)

create_tx = contract_api.create(identity, contract_source, init_resources = ["value"])

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

# create the tx
tx = create_json_tx(
    contract_name=source_digest + '.' + identity.public_key + '.increment',
    json_data={},
    resources=['value'],
)

# sign the transaction contents
tx.sign(identity.signing_key)

wire_fmt = json.loads(tx.to_wire_format())
print(wire_fmt)

# # submit that transaction
code, response = submit_json_transaction(HOST, PORT, wire_fmt)

print(code)
print(response)


while True:
    status = status_api.status(response['txs'][0])

    print(status)
    if status == "Executed":
        break

    time.sleep(1)

print('Query')

source_digest_hex = binascii.hexlify(base64.b64decode(source_digest)).decode()

url = 'http://{}:{}/api/contract/{}/{}/value'.format(HOST, PORT, source_digest_hex, identity.public_key_hex)

print(url)

r = status_api._session.post(url, json={})
print(r.status_code)
print(r.json())
