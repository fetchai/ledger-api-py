import os
import random
import json

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.crypto import Entity, Address
from fetchai.ledger.contract import SynergeticContract

CONTRACT_TEXT = """
@problem
function createProblem(data : Array<StructuredData>) : Int32
  var value = 0;
  for (i in 0:data.count() - 1)
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

"""


def main():
    # create the API
    api = LedgerApi('127.0.0.1', 8000)

    # create an entity and provide it some wealth
    print('Setup...')
    entity = Entity()
    api.sync(api.tokens.wealth(entity, 100000000))
    print('Setup...complete')

    # create the contract on the ledger
    synergy_contract = SynergeticContract(CONTRACT_TEXT)
    print(synergy_contract.digest)

    api.sync(api.contracts.create(entity, synergy_contract, 4096))

    # create a whole series of random data to submit to the DAG
    random_ints = [random.randint(0, 200) for _ in range(10)]
    api.sync([api.synergetic.submit_data(entity, synergy_contract.digest, value=value) for value in random_ints])


if __name__ == '__main__':
    main()
