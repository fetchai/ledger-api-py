from lark import Lark, tree, lexer
from pkg_resources import resource_string

# Utility function for checking if a node exists within a (sub)tree
def tree_contains(tree_root: tree.Tree, tree_node: tree.Tree):
    return tree_node in tree_root.iter_subtrees_topdown()


class AnnotatedTree:
    def __init__(self, parsed_tree: tree.Tree):
        pass


class Function:
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
            for t in node.children[0].children:
                if t.type == 'NAME':
                    items.append(parameter_dict[t.value])
                elif t.type == 'STRING_LITERAL':
                    items.append(StringLiteral(t.value))
            return StringConcat(items)

    def inject_parameters(self, par_dict):
        pass


class Parameter(ShardUse):
    def __init__(self, name, ptype, value=None):
        super().__init__()
        self.name = name
        self.ptype = ptype
        self.value = value

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


class EtchParser:
    def __init__(self, etch_code=None):
        # Load grammar
        self.grammar = resource_string(__name__, 'etch.grammar').decode('ascii')
        self.parser = Lark(self.grammar)

        self.parsed_tree = None
        if etch_code:
            self.parse(etch_code)

    def parse(self, etch_code):
        """Parses the input code and stores the parsed tree"""
        assert isinstance(etch_code, str), "Expecting string"
        self.parsed_tree = self.parser.parse(etch_code)
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

        # Get annotation nodes from parsed tree
        annotation_nodes = self.parsed_tree.find_data('annotation')

        for node in annotation_nodes:
            # Read annotation token for annotation type
            action_token = node.children[0]
            assert action_token.type == 'ANNOTATION'
            assert action_token.value in valid_entries
            action_type = action_token.value

            # Read function name token for annotation name
            function = node.children[1]
            function_name = function.children[0]
            assert function_name.type == 'NAME'
            action_name = function_name.value

            # Add to output dict
            entry_points[action_type].append(action_name)

        return entry_points

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
        parameters = [Parameter(p.children[0].value, p.children[1].value, parameter_values[i])
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
                assert g_name_node.children[1].type == 'TYPE'
                g_name = g_name_node.children[0].value
                g_type = g_name_node.children[1].value

            assert g_name not in persistent_globals, "Duplicate global definition: " + g_name
            persistent_globals[g_name] = PersistentGlobal(g_name, is_sharded, g_type)

        return persistent_globals

    def globals_used(self, entry_point, parameter_values):
        # First identify global definitions
        persistent_globals = self.globals_declared()

        # Now find use global statements within annotations
        annotation_node = next(self.parsed_tree.find_pred(
            lambda x: x.data == 'annotation' and x.children[1].children[0].value == entry_point))

        # Identify parameters of function
        parameters = {p.name: p for p in self.parameters(entry_point, parameter_values)}

        # Build list of globals used
        globals_used = []

        # Find all global use statements within function
        for gu in annotation_node.find_data('use_global'):
            assert isinstance(gu.children[0], lexer.Token) and gu.children[0].type == 'NAME', \
                "Could not identify global name"
            g_name = gu.children[0].value

            assert g_name in persistent_globals, "Attempting to use undeclared global"

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
