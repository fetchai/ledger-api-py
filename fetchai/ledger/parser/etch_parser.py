import logging
import re

from lark import Lark, tree, lexer, ParseError, GrammarError, LexError, UnexpectedInput, UnexpectedCharacters, \
    UnexpectedToken
from lark.exceptions import LarkError, VisitError
from pkg_resources import resource_string


# Utility function for checking if a node exists within a (sub)tree
def tree_contains(tree_root: tree.Tree, tree_node: tree.Tree):
    return tree_node in tree_root.iter_subtrees_topdown()


class AnnotatedTree:
    def __init__(self, parsed_tree: tree.Tree):
        pass


class ShardUse:
    """Class for representing and parsing legal persistent global shard use elements"""

    def __init__(self):
        self.value = ""

    @staticmethod
    def from_tree(node: tree.Tree, parameter_dict):
        assert node.data == 'use_shard_item'
        if isinstance(node.children[0], lexer.Token):
            if node.children[0].type == 'NAME':
                return parameter_dict[node.children[0].value]
            elif node.children[0].type == 'STRING_LITERAL':
                return StringLiteral(node.children[0].value)
        elif isinstance(node.children[0], tree.Tree):
            # String concat
            items = []
            logging.warning("global use statements including string-parameter concatenations are experimental")
            for t in node.children[0].children:
                if t.type == 'NAME':
                    items.append(parameter_dict[t.value])
                elif t.type == 'STRING_LITERAL':
                    items.append(StringLiteral(t.value))
            return StringConcat(items)

    def inject_parameters(self, par_dict):
        pass


def _template_to_string(node):
    if isinstance(node, lexer.Token):
        return node.value
    elif node.data == 'template_type':
        return node.children[0].value + '<' + _template_to_string(node.children[1]) + '>'
    elif node.data == 'template_arg_list':
        return ', '.join(_template_to_string(n) for n in node.children)


class Parameter(ShardUse):
    def __init__(self, name, ptype, value=None):
        super().__init__()
        self.name = name
        self.ptype = ptype
        self.value = value

    @staticmethod
    def from_tree(node, value=None):
        assert isinstance(node, tree.Tree), "Expecting Tree or Token object"

        # Extract parameter name
        name = node.children[0].value

        if isinstance(node.children[1], lexer.Token):
            # Simple typed parameter: extract type
            ptype = node.children[1].value
        else:
            # Template or other complex type
            if node.children[1].data == 'template_type':
                ptype = _template_to_string(node.children[1])
            else:
                raise RuntimeError("Unexpected input for Parameter.from_tree")

        return Parameter(name, ptype, value)

    def inject_parameters(self, par_dict):
        self.value = par_dict[self.name]


class StringLiteral(ShardUse):
    def __init__(self, value=""):
        super().__init__()
        self.value = value.strip("\'\"")


class StringConcat(ShardUse):
    def __init__(self, items: list):
        super().__init__()
        for i in items:
            assert isinstance(i, ShardUse)
        self.items = items

    @property
    def value(self):
        return ''.join(i.value for i in self.items)

    @value.setter
    def value(self, v):
        pass

    def inject_parameters(self, par_dict):
        for i in self.items:
            i.inject_parameters(par_dict)


class PersistentGlobal:
    def __init__(self, name, is_sharded=False, gtype=None):
        self.name = name
        self.is_sharded = is_sharded
        self.gtype = gtype


class Function:
    def __init__(self, name, parameters, return_type=None, annotation=None, code_block=None, lines=None):
        self.name = name
        self.parameters = parameters
        self.return_type = return_type
        self.annotation = annotation
        self.code_block = code_block
        self.lines = lines

    @staticmethod
    def from_tree(tree: tree.Tree):
        # Parse annotation parent node
        lines = (tree.line, tree.end_line)
        if tree.data == 'annotation':
            annotation = tree.children[0].value
            tree = tree.children[1]
        else:
            annotation = None

        # Parse function name
        assert tree.children[0].type == 'NAME'
        function_name = tree.children[0].value

        # Parse parameters
        assert tree.children[1].data == 'parameter_block', "Missing parameter block"
        parameters = [Parameter.from_tree(n) for n in tree.children[1].children]

        # Check for output type
        if len(tree.children) > 2 and isinstance(tree.children[2], lexer.Token):
            return_type = tree.children[2].value
        else:
            return_type = None

        # Store the parsed code block tree
        code_block = list(tree.find_data('code_block'))
        if len(code_block) == 0:
            code_block = None
        else:
            assert len(code_block) == 1, "Found more than one code block"
            code_block = code_block[0]

        return Function(function_name, parameters, return_type, annotation, code_block, lines=lines)

    @staticmethod
    def all_from_tree(tree: tree.Tree):
        """Returns a list of all functions within a parsed tree"""
        functions = []

        top_level = tree.find_data('top_level_instruction')
        for inst in top_level:
            if len(inst.children) > 0 and inst.children[0].data in ['annotation', 'function']:
                functions.append(Function.from_tree(inst.children[0]))

        return functions


class UseWildcardShardMask(Exception):
    pass


class UnparsableAddress(Exception):
    pass


class EtchParserError(Exception):
    pass


class EtchParser:
    def __init__(self, etch_code=None):
        # Load grammar
        self.grammar = resource_string(__name__, 'etch.grammar').decode('ascii')
        self.parser = Lark(self.grammar, propagate_positions=True)

        self._parsed_tree = None
        self.etch_code = None
        if etch_code:
            self.parse(etch_code)

    @property
    def parsed_tree(self):
        if self._parsed_tree:
            return self._parsed_tree
        else:
            raise EtchParserError()

    def parse(self, etch_code):
        """Parses the input code and stores the parsed tree"""
        assert isinstance(etch_code, str), "Expecting string"
        self.etch_code = etch_code
        try:
            self._parsed_tree = self.parser.parse(etch_code)
        except (LarkError, GrammarError, ParseError, LexError, UnexpectedInput,
                UnexpectedCharacters, UnexpectedToken, VisitError) as e:
            logging.warning("Etch parsing failed, shard masks will be set to wildcard")
            logging.warning(e)
            return False

        return self.parsed_tree

    def entry_points(self, valid_entries=None):
        """Identify annotated entry points"""
        # List of valid entry point types (TODO: expand for synergistic contracts)
        if not valid_entries:
            valid_entries = ['init', 'query', 'action']

        # Build dict of lists of entry points of each type
        entry_points = {}
        for ep in valid_entries:
            entry_points[ep] = []

        # Parse all functions in tree
        try:
            functions = self.get_functions()

            # Add functions with annotation to entry point dict
            for f in functions:
                if f.annotation in valid_entries:
                    entry_points[f.annotation].append(f.name)

        except EtchParserError:
            # Fallback method to extract entry points when parsing fails
            matches = re.findall(r'@([a-zA-Z]+)\nfunction ([a-zA-Z0-9]+)', self.etch_code)

            for ann, func in matches:
                if ann in valid_entries:
                    entry_points[ann].append(func)

        return entry_points

    def get_functions(self):
        """Returns a list of all functions found in source"""
        return Function.all_from_tree(self.parsed_tree)

    def subfunctions(self):
        """Identify functions that are not entry points"""
        functions = self.get_functions()
        return list(f.name for f in functions if f.annotation is None)

    def global_using_subfunctions(self):
        """Return a dict of non entry functions, listing any global use statements they contain"""
        globals_used = {}

        functions = self.get_functions()

        for f in functions:
            if f.annotation:
                # Skip annotated functions
                continue

            use_statements = f.code_block.find_data('use_global')
            if len(list(use_statements)):
                globals_used[f.name] = []  # TODO: Later expand with details of globals used

        return globals_used

    def parameters(self, function_name: str, parameter_values: list = None):
        """Identify parameters accepted by a named function"""
        # Get nodes for all functions
        functions = list(self.parsed_tree.find_data('function'))

        # Find the function requested
        matching = next(f for f in functions
                        if isinstance(f.children[0], lexer.Token)
                        and f.children[0].value == function_name)

        # Extract parameter block node
        assert matching.children[1].data == 'parameter_block'
        parameter_tokens = matching.children[1].children

        # If no parameter values passed, default to None
        if not parameter_values:
            parameter_values = [None] * len(parameter_tokens)

        # Check that if parameter values were given, they match the number of parameters found
        assert len(parameter_values) == len(parameter_tokens), \
            "Found {} parameters, but received {} parameter values".format(len(parameter_tokens), len(parameter_values))

        # Unpack typed parameters and add values
        parameters = [Parameter.from_tree(p, value=parameter_values[i])
                      for i, p in enumerate(parameter_tokens)]

        return parameters

    def globals_declared(self):
        """Identify persistent globals declared"""
        global_defs = self.parsed_tree.find_data('global_def')

        # List of declared globals
        persistent_globals = {}

        for gd in global_defs:
            # Does global have the sharded qualifier
            is_sharded = isinstance(gd.children[0], lexer.Token) and gd.children[0].value == 'sharded'

            # Retrieve name node from tree
            g_name_node = gd.children[1 * is_sharded]

            # This may either be a typed or untyped name
            if isinstance(g_name_node, lexer.Token):
                # TODO: Is an untyped global legal?
                g_name = g_name_node.value
                g_type = None
            else:
                assert g_name_node.children[0].type == 'NAME'
                g_name = g_name_node.children[0].value
                g_type = _template_to_string(g_name_node.children[1])

            assert g_name not in persistent_globals, "Duplicate global definition: " + g_name
            persistent_globals[g_name] = PersistentGlobal(g_name, is_sharded, g_type)

        return persistent_globals

    def globals_used(self, entry_point, parameter_values):
        if 'State' in self.etch_code:
            raise UseWildcardShardMask("State usage detected")

        # First identify global definitions
        persistent_globals = self.globals_declared()

        # Now find use global statements within annotations
        annotation_node = next(self.parsed_tree.find_pred(
            lambda x: x.data == 'annotation' and x.children[1].children[0].value == entry_point))

        # Identify parameters of function
        assert isinstance(parameter_values, list), "Expected parameter values as a list"
        parameters = {p.name: p for p in self.parameters(entry_point, parameter_values)}

        # Parse for functions called (TODO: refactor as class)
        function_calls = annotation_node.find_data('function_call')
        called_names = []
        for f in function_calls:
            function_name = list(f.children[0].scan_values(lambda t: isinstance(t, lexer.Token) and t.type == 'NAME'))
            # len > 1 indicates dot-expanded name, assumed non-user defined, therefore not containing use statements
            if len(function_name) == 1:
                called_names.append(function_name[0].value)
        # If any called functions use globals, we currently can't parse those usages
        if any(fn in called_names for fn in self.global_using_subfunctions()):
            raise UnparsableAddress("Calls global using subfunction")

        # Build list of globals used
        globals_used = []

        # Find all global use statements within function
        for gu in annotation_node.find_data('use_global'):
            assert isinstance(gu.children[0], lexer.Token) and gu.children[0].type == 'NAME', \
                "Could not identify global name"
            g_name = gu.children[0].value

            # Handle use any
            if g_name == 'any' and len(gu.children) == 1:
                # Check if we have any sharded globals
                if any(pg for pg in persistent_globals.values() if pg.is_sharded):
                    raise UseWildcardShardMask("use any + persistent sharded global")

                # If we don't have sharded globals, add all globals to used list
                globals_used = [g_name for g_name in persistent_globals.keys()]
                # Return immediately as we're already using all globals
                return globals_used

            assert g_name in persistent_globals, "Attempting to use undeclared global : {}".format(gu)

            # Handle non-sharded global
            if not persistent_globals[g_name].is_sharded:
                assert len(gu.children) == 1, "Sharded use statement for non-sharded global: " + g_name
                globals_used.append(g_name)

            # Handle sharded global
            else:
                # TODO: assert that any parameters used in shard access are never the target of an assignment
                assert len(gu.children) > 1, "Non-sharded use statement for sharded global: " + g_name
                shards = gu.find_data('use_shard_item')

                for sh in shards:
                    globals_used.append((g_name, ShardUse.from_tree(sh, parameters)))

        return globals_used

    def used_globals_to_addresses(self, entry_point, parameters: list):
        # Identify globals used in function
        used_globals = self.globals_used(entry_point, parameters)
        # Build list of state addresses
        addresses = []

        # Replace parameters and strings with values
        for usage in used_globals:
            # Tuples represent sharded globals
            if isinstance(usage, tuple):
                address = '{}.{}'.format(usage[0], usage[1].value)

                addresses.append(address)
            # Single strings represent non-sharded globals
            elif isinstance(usage, str):
                addresses.append(usage)
            else:
                raise NotImplementedError()

        return addresses
