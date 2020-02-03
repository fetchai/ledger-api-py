import unittest
from unittest.mock import patch

from lark import GrammarError, ParseError, UnexpectedCharacters

from fetchai.ledger.parser.etch_parser import EtchParser, Function

CONTRACT_TEXT = """
persistent sharded balance_state : UInt64;
persistent owner_name : String;

@init
function setup(owner : Address)
  use balance_state[owner];
  balance_state.set(owner, 1000000u64);
endfunction

@action
function transfer(from: Address, to: Address, amount: UInt64)
  use owner_name;  // inline comment
  use balance_state[from, to, "constant_string", "prefix." + to];

  // Check if the sender has enough balance to proceed
  if (balance_state.get(from) >= amount)

    // update the account balances
    balance_state.set(from, balance_state.get(from) - amount);
    balance_state.set(to, balance_state.get(to, 0u64) + amount);
  endif

endfunction

@query
function balance(address: Address) : UInt64
    use balance_state[address];
    return balance_state.get(address, 0u64);
endfunction

function sub(val1: UInt64, val2: UInt64) : UInt64
    return val1 - val2;
endfunction
"""

# Function block template - for testing statements that are illegal outside a function
FUNCTION_BLOCK = """function a()
{}
endfunction
"""

NESTED_FUNCTION = """
@action
function set_block_number_state()
  State<UInt64>('block_number_state').set(getBlockNumber());
endfunction

@query
function query_block_number_state() : UInt64
  return State<UInt64>('block_number_state').get(0u64);
endfunction"""

TEMPLATE_GLOBAL = """
persistent users : Array<Address>;
persistent sharded sharded_users : Array<Address>;
@action
function A()
    use users;
endfunction

@action
function B()
    use sharded_users['abc'];
endfunction
"""


class ParserTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.parser = EtchParser(CONTRACT_TEXT)
            self.assertIsNotNone(self.parser._parsed_tree, "Parsed tree missing when code passed")
        except ParseError as e:
            self.fail("Failed to parse contract text: \n" + str(e))

    def test_grammar(self):
        """Check that grammer compiles"""
        # TODO: Grammar is loaded from a file, which may impact unit test performance
        try:
            parser = EtchParser()
            self.assertIsNone(parser._parsed_tree, "Parsed tree present when no code passed")
        except GrammarError as e:
            self.fail("Etch grammar failed to load with: \n" + str(e))

    def test_get_functions(self):
        """Check that functions properly identified"""
        functions = self.parser.get_functions()

        # Check all functions found
        function_dict = {f.name: f for f in functions}
        self.assertTrue(all(n in function_dict.keys() for n in ['setup', 'transfer', 'balance', 'sub']))

        # Check transfer parsed
        self.assertEqual(function_dict['transfer'].annotation, 'action')
        self.assertEqual(function_dict['transfer'].lines, (11, 24))
        self.assertIsNotNone(function_dict['transfer'].code_block)

        # Check return value correctly parsed
        self.assertEqual(function_dict['balance'].return_type, 'UInt64')

        # Check parameter block correctly parsed
        self.assertEqual(len(function_dict['setup'].parameters), 1)
        self.assertIsNone(function_dict['setup'].parameters[0].value)
        self.assertEqual(function_dict['setup'].parameters[0].name, 'owner')
        self.assertEqual(function_dict['setup'].parameters[0].ptype, 'Address')

    def test_entry_points(self):
        entry_points = self.parser.entry_points()
        self.assertIn('init', entry_points)
        self.assertIn('action', entry_points)
        self.assertIn('query', entry_points)

        self.assertEqual(entry_points['init'], ['setup'])
        self.assertEqual(entry_points['action'], ['transfer'])
        self.assertEqual(entry_points['query'], ['balance'])

    def test_globals_declared(self):
        glob_decl = self.parser.globals_declared()
        self.assertEqual(set(glob_decl.keys()), {'balance_state', 'owner_name'})
        self.assertEqual(glob_decl['balance_state'].name, 'balance_state')
        self.assertEqual(glob_decl['balance_state'].gtype, 'UInt64')
        self.assertEqual(glob_decl['balance_state'].is_sharded, True)

        self.assertEqual(glob_decl['owner_name'].name, 'owner_name')
        self.assertEqual(glob_decl['owner_name'].gtype, 'String')
        self.assertEqual(glob_decl['owner_name'].is_sharded, False)

    def test_globals_used(self):
        """Test accurate parsing of globals used in entry points"""
        # Test accurate parsing of declared globals
        glob_used = self.parser.globals_used('setup', ['abc'])
        self.assertEqual(len(glob_used), 1)
        self.assertEqual(len(glob_used[0]), 2)
        self.assertEqual(glob_used[0][0], 'balance_state')
        self.assertEqual(glob_used[0][1].value, 'abc')
        self.assertEqual(glob_used[0][1].name, 'owner')

    def test_global_addresses(self):
        """Test accurate parsing of globals used in entry points"""

        with patch('logging.warning') as mock_warn:
            glob_addresses = self.parser.used_globals_to_addresses('transfer', ['abc', 'def', 100])
            self.assertEqual(mock_warn.call_count, 1)
        self.assertEqual(len(glob_addresses), 5)
        # Unsharded use statement
        self.assertEqual(glob_addresses[0], 'owner_name')
        # Sharded use statements
        self.assertEqual(glob_addresses[1], 'balance_state.abc')  # Parameter
        self.assertEqual(glob_addresses[2], 'balance_state.def')  # Parameter
        self.assertEqual(glob_addresses[3], 'balance_state.constant_string')  # String constant
        self.assertEqual(glob_addresses[4], 'balance_state.prefix.def')  # String concatenation

    def test_scope(self):
        """Tests which instructions are allowed at each scope"""
        # Regular instructions are not allowed at global scope
        with patch('logging.warning') as mock_warn:
            self.assertFalse(self.parser.parse("var a = 5;"))
            self.assertEqual(mock_warn.call_count, 2)

        # Allowed at global scope
        try:
            # Persistent global declaration
            self.assertTrue(self.parser.parse("persistent sharded balance_state : UInt64;")
                            is not False)
            self.assertTrue(self.parser.parse("persistent owner : String;")
                            is not False)

            # Functions
            self.assertTrue(
                self.parser.parse("""function a(owner : String)
                var b = owner;
                endfunction""")
                is not False)

            # Annotated functions
            self.assertTrue(
                self.parser.parse("""@action
                function a(owner : String)
                var b = owner;
                endfunction""")
                is not False)

            # Comments
            self.assertTrue(self.parser.parse("// A comment")
                            is not False)
        except UnexpectedCharacters as e:
            self.fail("Etch parsing of top level statement failed: \n" + str(e))

    def test_builtins(self):
        """Tests for correct parsing of all supported builtin types"""
        parser = EtchParser()
        int_types = ['Int' + str(x) for x in [8, 16, 32, 64, 256]]
        uint_types = ['UInt' + str(x) for x in [8, 16, 32, 64, 256]]

        float_types = ['Float' + str(x) for x in [32, 64]]
        fixed_types = ['Fixed' + str(x) for x in [32, 64]]

        # Test declaration of numerical types
        for t in int_types + uint_types:
            tree = self.parser.parse(FUNCTION_BLOCK.format("var a : {};".format(t)))
            tree = next(tree.find_data("instruction"))
            self.assertEqual(tree.children[0].data, 'declaration')
            self.assertEqual(tree.children[0].children[1].type, 'BASIC_TYPE')
            self.assertEqual(tree.children[0].children[1].value, t)

        for t in float_types:
            tree = self.parser.parse(FUNCTION_BLOCK.format("var a : {};".format(t)))
            tree = next(tree.find_data("instruction"))
            self.assertEqual(tree.children[0].data, 'declaration')
            self.assertEqual(tree.children[0].children[1].type, 'FLOAT_TYPE')
            self.assertEqual(tree.children[0].children[1].value, t)

        for t in fixed_types:
            tree = self.parser.parse(FUNCTION_BLOCK.format("var a : {};".format(t)))
            tree = next(tree.find_data("instruction"))
            self.assertEqual(tree.children[0].data, 'declaration')
            self.assertEqual(tree.children[0].children[1].type, 'FIXED_TYPE')
            self.assertEqual(tree.children[0].children[1].value, t)

        # Test declaration of other types
        other_types = ['Boolean', 'String']
        for t in other_types:
            tree = self.parser.parse(FUNCTION_BLOCK.format("var a : {};".format(t)))
            tree = next(tree.find_data("instruction"))
            self.assertEqual(tree.children[0].data, 'declaration')
            self.assertEqual(tree.children[0].children[1].type, 'NAME')
            self.assertEqual(tree.children[0].children[1].value, t)

        # TODO: Test these in a meaningful way, beyond simply that they parse
        # Test declaration of array
        tree = self.parser.parse(FUNCTION_BLOCK.format("var myArray = Array<Int32>(5);"))
        # Test assignment to array
        tree = self.parser.parse(FUNCTION_BLOCK.format("myArray[0] = 5;"))
        # Test assignment from array
        tree = self.parser.parse(FUNCTION_BLOCK.format("b = myArray[0];"))
        tree = self.parser.parse(FUNCTION_BLOCK.format("var b = myArray[0];"))

        # As above, for map type
        tree = self.parser.parse(FUNCTION_BLOCK.format("var myArray = Map<String, Int32>(5);"))
        # Test assignment to array
        tree = self.parser.parse(FUNCTION_BLOCK.format("myArray['test'] = 5;"))
        # Test assignment from array
        tree = self.parser.parse(FUNCTION_BLOCK.format("b = myArray['test'];"))
        tree = self.parser.parse(FUNCTION_BLOCK.format("var b = myArray['test'];"))

    def test_instantiation(self):
        """Tests for correct parsing of valid variable instantiation"""
        # Check that the following parse without error
        tree = self.parser.parse(FUNCTION_BLOCK.format("var b = get();"))  # Untyped instantiation
        tree = self.parser.parse(FUNCTION_BLOCK.format("var b : UInt64 = get();"))  # Typed instantiation

    def test_template(self):
        """Tests for correct parsing of template variables"""
        tree = self.parser.parse(FUNCTION_BLOCK.format("a = State<UInt64>();"))
        tree = self.parser.parse(FUNCTION_BLOCK.format("a = State<UInt64, UInt64>();"))

        # Test function parsing with template parameters
        tree = self.parser.parse("""function a(b : Array<StructuredData>) : Int32
        var c : State<UInt32>;
        endfunction
        """)
        functions = self.parser.get_functions()

        # Check that argument list correctly parsed
        self.assertEqual(functions[0].parameters[0].name, 'b')
        self.assertEqual(functions[0].parameters[0].ptype, 'Array<StructuredData>')

    def test_functions(self):
        """Tests correct detection of non-entry-point functions"""
        self.assertEqual(self.parser.subfunctions(), ['sub'])

    def test_class_function(self):
        """Tests correct ingestion of functions"""
        # Test minimal function
        tree = self.parser.parse("""function init()
        endfunction""")

        func = Function.from_tree(next(tree.find_data('function')))

        self.assertIsNone(func.annotation)
        self.assertIsNone(func.code_block)
        self.assertIsNone(func.return_type)
        self.assertEqual(func.name, 'init')
        self.assertEqual(func.parameters, [])

        # Test Function parsing from_tree
        tree = self.parser.parse("""
        @action
        function a(b : UInt64) : String
        return b;
        endfunction
        """)
        func = Function.from_tree(next(tree.find_data('annotation')))
        self.assertEqual(func.name, 'a')
        self.assertEqual(func.return_type, 'String')
        self.assertEqual(func.annotation, 'action')
        self.assertEqual(func.parameters[0].name, 'b')
        self.assertEqual(func.parameters[0].ptype, 'UInt64')

        # Test all_from_tree
        tree = self.parser.parse("""
        @action
        function a(b : UInt64) : String
        return 'test';
        endfunction
        
        function c(d: UInt64): String
        return 'test2';
        endfunction
        """)

        funcs = Function.all_from_tree(tree)
        self.assertEqual(funcs[0].name, 'a')
        self.assertEqual(funcs[0].return_type, 'String')
        self.assertEqual(funcs[0].annotation, 'action')
        self.assertEqual(funcs[0].parameters[0].name, 'b')
        self.assertEqual(funcs[0].parameters[0].ptype, 'UInt64')

        self.assertEqual(funcs[1].name, 'c')
        self.assertEqual(funcs[1].return_type, 'String')
        self.assertIsNone(funcs[1].annotation)
        self.assertEqual(funcs[1].parameters[0].name, 'd')
        self.assertEqual(funcs[1].parameters[0].ptype, 'UInt64')

    def test_nested_function_call(self):
        """Check that nested function calls are supported by parser"""
        try:
            tree = self.parser.parse(NESTED_FUNCTION)
            self.assertTrue(tree is not False)
        except:
            self.fail("Parsing of dot nested function calls failed")

    def test_expressions(self):
        """Check that common expressions parse correctly"""
        # Instantiation
        tree = self.parser.parse(FUNCTION_BLOCK.format("var a = 1i32;"))
        # Binary operation
        tree = self.parser.parse(FUNCTION_BLOCK.format("var a = 1i32 + 2i32;"))
        # Pre-unary operation
        tree = self.parser.parse(FUNCTION_BLOCK.format("var a = - 2i32;"))
        # Post-unary operation
        tree = self.parser.parse(FUNCTION_BLOCK.format("var a = 2i32++;"))
        # Comparison operation
        tree = self.parser.parse(FUNCTION_BLOCK.format("var a = 2i32 == 3i32;"))
        # Type cast
        tree = self.parser.parse(FUNCTION_BLOCK.format("var a = Int64(3i32);"))

    def test_assignments(self):
        """Check successful parsing of assignment operators"""
        FB_WITH_DECLARATION = FUNCTION_BLOCK.format("var a : Int64; {}")
        tree = self.parser.parse(FB_WITH_DECLARATION.format("a += 5;"))
        tree = self.parser.parse(FB_WITH_DECLARATION.format("a -= 5;"))
        tree = self.parser.parse(FB_WITH_DECLARATION.format("a *= 5;"))
        tree = self.parser.parse(FB_WITH_DECLARATION.format("a /= 5;"))
        tree = self.parser.parse(FB_WITH_DECLARATION.format("a %= 5;"))

    def test_assert_statement(self):
        """Check boolean expressions valid in any context"""
        tree = self.parser.parse(FUNCTION_BLOCK.format("assert(a >= 0 && a <= 15);"))

    def test_template_global(self):
        """Checks correct parsing of globals with template types"""
        self.parser.parse(TEMPLATE_GLOBAL)

        # Function A contains a non-sharded global of type Array<Address>
        addresses = self.parser.used_globals_to_addresses('A', [])
        self.assertEqual(addresses, ['users'])

        # Function B contains a sharded global of type Array<Address>
        addresses = self.parser.used_globals_to_addresses('B', [])
        self.assertEqual(addresses, ['sharded_users.abc'])

    def test_if_blocks(self):
        """Checks correct parsing of if blocks"""
        # Partial contract text with function block and variable instantiation
        PARTIAL_BLOCK = FUNCTION_BLOCK.format("""
        var a: Int64 = 5;
        var b: Int64 = 0;
        {}""")

        # Simple if block
        tree = self.parser.parse(PARTIAL_BLOCK.format("""
        if (a > 5)
            b = 6;
        endif"""))
        self.assertTrue(tree is not False)

        # If-else block
        tree = self.parser.parse(PARTIAL_BLOCK.format("""
        if (a > 5)
            b = 6;
        else
            b = 7;
        endif"""))
        self.assertTrue(tree is not False)

        # Nested if-else-if block
        tree = self.parser.parse(PARTIAL_BLOCK.format("""
        if (a > 5)
            b = 6;
        else if (a < 5)
                b = 4;
            endif
        endif"""))
        self.assertTrue(tree is not False)

        # If-elseif block
        tree = self.parser.parse(PARTIAL_BLOCK.format("""
        if (a > 5)
            b = 6;
        elseif (a < 5)
            b = 4;
        endif"""))
        self.assertTrue(tree is not False)

        # Complex example
        tree = self.parser.parse(PARTIAL_BLOCK.format("""
        if (a > 5 && a < 100)
            b = 6;
        elseif (a < 2 || a > 100)
            if (a < 0)
                b = 4;
            else
                b = 2;
            endif
        else
            b = 3;
        endif"""))
        self.assertTrue(tree is not False)

    def test_warn_on_parse_fail(self):
        with patch('logging.warning') as mock_warn:
            tree = self.parser.parse("This code is not valid")
            self.assertFalse(tree)
            self.assertEqual(mock_warn.call_count, 2)
