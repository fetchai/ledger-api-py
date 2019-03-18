contract_source = """

// On init triggered on the creation of a smart contract - will set the owner.
@on_init
function on_init(owner : Address)
  Print("on_init triggered, owner is: " + owner.AsString());

  // Set the owner
  var owner_state = State<Address>("owner", Address());
  owner_state.set(owner);

  // Set the balance of the owner
  var balances = State<Int32>(owner.AsString(), 1);
  balances.set(2009);
endfunction

@action
function transfer(from : Address, to : Address, amount : Int32) : Int32
  var owner_state = State<Address>("owner", Address());

  Print("From address is signed? : " + toString(from.signed_tx()));
  Print("To address is signed? : " + toString(to.signed_tx()));
  Print("Transferring " + toString(amount) +" from "+ from.AsString() + " to: " + to.AsString());

  if(owner_state.get().AsString() == from.AsString())
    Print("Owner making the call");
  else
    Print("Owner not making the call");
  endif

  if(!from.signed_tx())
    Print("*** From address not verified! Quitting. ***");
    return 1;
  endif

  var balance_from = State<Int32>(from.AsString(), 0);
  var balance_to   = State<Int32>(to.AsString(), 0);

  Print("Initial balance: " + toString(balance_from.get()));

  if(balance_from.get() < amount)
    Print("Failed! Not enough funds");
    return 1;
  endif

  balance_from.set(balance_from.get() - amount);
  balance_to.set(balance_to.get() + amount);

  Print("Final balance: " + toString(balance_from.get()));
  Print("Success!");

  return 0;
endfunction

// Allow clients to query the amount the owner has
@query
function owner_funds() : Int32

  var balance = State<Int32>(State<Address>("owner", Address()).get().AsString(), 0);
  var bal = balance.get();

  Print("query triggered for owner balance: " + toString(bal));
  return bal;
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
    print(wire_fmt)

    # # submit that transaction
    code = submit_json_transaction(HOST, PORT, wire_fmt)

    print(code)

    time.sleep(5)

print('Query for owner funds')

source_digest_hex = binascii.hexlify(base64.b64decode(source_digest)).decode()

url = 'http://{}:{}/api/contract/{}/{}/owner_funds'.format(HOST, PORT, source_digest_hex, identity.public_key_hex)

print(url)

r = status_api._session.post(url, json={})
print(r.status_code)
print(r.json())
