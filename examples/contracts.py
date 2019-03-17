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
  balances.set(2002);

  // aside - write to 'value' so as to later test query functionality
  var state = State<Int32>("value", 100000);
  state.set(state.get());
endfunction

@action
function transfer(from : Address, to : Address, amount : Int32) : Int32
  var default = Address();
  var owner_state = State<Address>("owner", default);

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

// Test arbitrary numbers of parameters, incrementing state
@action
function increment(input_a : Int32, input_b : Int32, input_c : Int32)
  var state = State<Int32>("value", 10);
  Print("Increment triggering");
  Print(toString(input_c));
  state.set(state.get() + 1000 + input_c);

  var default = Address();
  Print("CONS.");
  var owner_state = State<Address>("owner", default);
  Print("CONS2.");
  Print("We recognise owner as: " + owner_state.get().AsString());
endfunction

@query
function value() : Int32
  var state = State<Int32>("value", 12);
  Print("query triggered.");
  return state.get();
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

create_tx = contract_api.create(identity, contract_source, init_resources = ["value", "owner", identity.public_key])

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
    json_data=msgpack.packb([10, 20, 30], use_bin_type=True),
    resources=['value', 'owner'],
    raw_resources=[source_digest],
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

print('transfer N times')

for index in range(50):

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
    code, response = submit_json_transaction(HOST, PORT, wire_fmt)

    print(code)
    print(response)

    time.sleep(5)
