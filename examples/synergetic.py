import os

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.crypto import Entity, Address
from fetchai.ledger.contract import SynergeticContract

CONTRACT_TEXT = """
@problem
function dagState() : Int32
    return 0;
endfunction

@objective
function proofOfWork(problem : Int32, solution : Int32 ) : Int64 
    return abs(toInt64(problem) - toInt64(solution));
endfunction

@clear
function applyWork(problem : Int32, solution : Int32)
endfunction

@work
function mineWork(problem : Int32, nonce : BigUInt) :  Int32
  return nonce.toInt32();
endfunction

@generator
function makeDAGnode(epoch : Int32, entropy : BigUInt)
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
    random_data = ['foo bar is a baz {}'.format(n).encode('ascii') for n in range(1)]
    api.sync([api.synergetic.submit_data(entity, synergy_contract.digest, data) for data in random_data])


if __name__ == '__main__':
    main()
