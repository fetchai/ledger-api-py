import unittest

from lark import GrammarError, ParseError

from fetchai.ledger.parser.etch_parser import EtchParser

CONTRACT_TEXT = """
persistent sharded balance : UInt64;

@init
function setup(owner : Address)
  use balance[owner];
  balance.set(owner, 1000000u64);
endfunction

@action
function transfer(from: Address, to: Address, amount: UInt64)

  use balance[from, to];

  var a = State<UInt64>()
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


class ParserTests(unittest.TestCase):
    def test_grammar(self):
        """Check that grammer compiles"""
        # TODO: Grammar is loaded from a file, which may impact unit test performance
        try:
            parser = EtchParser()
            self.assertIsNone(parser.parsed_tree, "Parsed tree present when no code passed")
        except GrammarError as e:
            self.fail("Etch grammar failed to load with: \n" + str(e))

    def test_parse_contract(self):
        """Tests for successful parsing of example contract text"""
        try:
            parser = EtchParser(CONTRACT_TEXT)
            self.assertIsNotNone(parser.parsed_tree, "Parsed tree missing when code passed")
        except ParseError as e:
            self.fail("Failed to parse contract text: \n" + str(e))

    def test_parse(self):
        """Tests for proper parsing of minimal code snippets"""
        # Persistent global declarations

    def test_builtins(self):
        """Tests for correct parsing of all supported builtin types"""
        parser = EtchParser()
        int_types = ['Int' + str(x) for x in [8, 16, 32, 64, 256]]
        uint_types = ['UInt' + str(x) for x in [8, 16, 32, 64, 256]]

        float_types = ['Float' + str(x) for x in [32, 64]]
        fixed_types = ['Fixed' + str(x) for x in [32, 64]]

        # Test declaration of numerical types
        for t in int_types + uint_types + float_types + fixed_types:
            tree = parser.parse("var a : {};".format(t))

            self.assertEqual(tree.children[0].data, 'declaration')
            self.assertEqual(tree.children[0].children[1].type, 'TYPE')
            self.assertEqual(tree.children[0].children[1].value, t)

        # Test declaration of other types
        other_types = ['Boolean', 'String']
        for t in other_types:
            tree = parser.parse("var a : {};".format(t))

            self.assertEqual(tree.children[0].data, 'declaration')
            self.assertEqual(tree.children[0].children[1].type, 'TYPE')
            self.assertEqual(tree.children[0].children[1].value, t)

        # Test declaration of array
        array_types = 'Array'
        map_type = 'Map'
        # TODO

    def test_inline(self):
        """Tests for correct parsing of inline type annotations"""


if __name__ == '__main__':
    unittest.main()
