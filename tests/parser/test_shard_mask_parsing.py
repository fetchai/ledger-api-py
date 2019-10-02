import unittest

from lark import ParseError

from fetchai.ledger.parser.etch_parser import EtchParser, UseWildcardShardMask, UnparsableAddress

CONTRACT_TEXT = """
persistent sharded balance : UInt64;
persistent owner_name : String;

@init
function setup(owner : Address)
  use balance[owner];
  balance.set(owner, 1000000u64);
endfunction

@action
function transfer(from: Address, to: Address, amount: UInt64)

  use balance[from, to];

  // Check if the sender has enough balance to proceed
  if (balance.get(from) >= amount)

    // update the account balances
    balance.set(from, balance.get(from) - amount);
    balance.set(to, balance.get(to, 0u64) + amount);
  endif

endfunction

@query
function balance(address: Address) : UInt64
    use balance[address];
    return balance.get(address, 0u64);
endfunction

"""

# For testing use statements outside annotated functions
# @init-setup() calls set_balance(), which uses a global outside an annotated function
# @action-transfer() uses globals directly, and calls the sub(), which doesn't use globals
NON_ENTRY_GLOBAL = """
persistent sharded balance : UInt64;

@init
function setup(owner : Address)
  set_balance(owner, 1000000u64);
endfunction

function set_balance(owner: Address, value: UInt64)
    use balance[owner];
    balance.set(owner, value);
endfunction

@action
function transfer(from: Address, to: Address, amount: UInt64)

  use balance[from, to];

  // Check if the sender has enough balance to proceed
  if (balance.get(from) >= amount)

    // update the account balances
    balance.set(from, sub(balance.get(from), amount));
    balance.set(to, balance.get(to, 0u64) + amount);
  endif

endfunction

function sub(val1 : UInt64, val2 : UInt64) : UInt64
    return val1 - val2;
endfunction 
"""

USE_ANY_NON_SHARDED = """
persistent var1 : UInt64;
persistent var2 : UInt64;

@action
function swap()
    use any;
    
    var1.set(var2.get());
endfunction
"""

USE_ANY_SHARDED = """
persistent sharded balance : UInt64;
persistent var3 : UInt64;

@action
function swap()
    use any;
    
    balance.set('var1', balance.get('var2', 0));
endfunction
"""


class ShardMaskParsingTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.parser = EtchParser()
            self.assertIsNone(self.parser.parsed_tree, "Unexpected initialisation of parsed tree")
        except ParseError as e:
            self.fail("Parser isntantiation failed with: \n" + str(e))

    def test_outside_annotation(self):
        """Test handling of calls to subfunctions containing use statements"""
        self.parser.parse(NON_ENTRY_GLOBAL)

        # Detect call to non-entry function that uses globals
        with self.assertRaises(UnparsableAddress):
            glob_used = self.parser.globals_used('setup', ['abc'])
            self.assertEqual(len(glob_used), 0, "Unexpected used globals found when declared in non annotated function")

        # Test transfer function, which calls a non-global-using subfunction
        glob_used = self.parser.globals_used('transfer', ['abc', 'def', 100])
        self.assertEqual('{}.{}'.format(glob_used[0][0], glob_used[0][1].value), 'balance.abc')
        self.assertEqual('{}.{}'.format(glob_used[1][0], glob_used[1][1].value), 'balance.def')

    def test_global_using_subfunctions(self):
        """Test detection of non-annotated functions containing 'use' statements"""
        self.parser.parse(NON_ENTRY_GLOBAL)

        # List of non-annotated functions that use globals
        global_using_subfunctions = self.parser.global_using_subfunctions()
        self.assertIn('set_balance', global_using_subfunctions)
        self.assertNotIn('sub', global_using_subfunctions)

        # Test that wildcard used when annotated function calls global using subfunction
        with self.assertRaises(UnparsableAddress):
            self.parser.used_globals_to_addresses('setup', ['abc'])

        # Parsing of function that doesn't call global-using-subfunction should succeed
        glob_addresses = self.parser.used_globals_to_addresses('transfer', ['abc', 'def', 100])
        self.assertEqual(glob_addresses, ['balance.abc', 'balance.def'])

    def test_use_any(self):
        """Test correct handling of 'use any'"""
        self.parser.parse(USE_ANY_NON_SHARDED)

        # Test correct detection of all persistent globals when none are sharded
        used_globals = self.parser.globals_used('swap', [])
        self.assertEqual(set(used_globals), {'var1', 'var2'})

        # Test correct raising of wildcard-needed exception if any globals are sharded
        self.parser.parse(USE_ANY_SHARDED)
        with self.assertRaises(UseWildcardShardMask):
            used_globals = self.parser.globals_used('swap', [])

    def test_use_state(self):
        pass

    def test_use_sharded_state(self):
        pass