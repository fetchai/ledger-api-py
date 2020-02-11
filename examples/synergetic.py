import random

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity

CONTRACT_TEXT = """\
@problem
function createProblem(data : Array<StructuredData>) : Int32
  var value = 0;
  for (i in 0:data.count())
    value += data[i].getInt32("value");
  endfor
  return value;
endfunction

@objective
function evaluateWork(problem : Int32, solution : Int32 ) : Int64
  return abs(toInt64(problem) - toInt64(solution));
endfunction

@work
function doWork(problem : Int32, nonce : UInt256) :  Int32
  return nonce.toInt32();
endfunction

@clear
function applyWork(problem : Int32, solution : Int32)
  var result = State<Int32>("solution");
  result.set(solution);
endfunction

@query
function query_result() : Int32
  var result = State<Int32>("solution");
  return result.get(-1);
endfunction
"""


def main():
    # create the API
    api = LedgerApi('127.0.0.1', 8000)

    # create an entity from a private key stored in hex
    entity = Entity.from_hex('6e8339a0c6d51fc58b4365bf2ce18ff2698d2b8c40bb13fcef7e1ba05df18e4b')

    # create the contract on the ledger
    synergetic_contract = Contract(CONTRACT_TEXT, entity)
    print('Creating contract..')
    api.sync(api.contracts.create(entity, synergetic_contract, 4096))

    # create a whole series of random data to submit to the DAG
    random_ints = [random.randint(0, 200) for _ in range(10)]
    fee = 100000000
    api.sync(
        [api.contracts.submit_data(entity, synergetic_contract.digest, synergetic_contract.address, fee, value=value) \
         for value in random_ints])
    print('Data submitted.')

    print('Waiting...')
    api.wait_for_blocks(10)

    print('Issuing query...')
    result = synergetic_contract.query(api, 'query_result')
    print('Query result:', result)


if __name__ == '__main__':
    main()
