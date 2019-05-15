import unittest

from fetchai.ledger.contract import SmartContract

SIMPLE_TOKEN_CONTRACT = """
@init
function setup(owner : Address)
  var owner_balance = State<UInt64>(owner, 0u64);
  owner_balance.set(1000000u64);
endfunction

@action
function transfer(from: Address, to: Address, amount: UInt64)

  // define the accounts
  var from_account = State<UInt64>(from, 0u64);
  var to_account = State<UInt64>(to, 0u64); // if new sets to 0u

  // Check if the sender has enough balance to proceed
  if (from_account.get() >= amount)
  
    // update the account balances
    from_account.set(from_account.get() - amount);
    to_account.set(to_account.get() + amount);
  endif

endfunction

@query
function balance(address: Address) : UInt64
    var account = State<UInt64>(address, 0u64);
    return account.get();
endfunction

"""


class SmartContractTests(unittest.TestCase):
    def test_empty(self):
        pass
        # contract = SmartContract(SIMPLE_TOKEN_CONTRACT)
        # self.assertEqual('40cea0c2002270c0a0c86d4d4c9c8d8b5df6e90b99327ccf91b21ffd1d700372', contract.digest)
