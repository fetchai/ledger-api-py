import unittest

from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity

CONTRACT_TEXT = """
@init
function init()
endfunction

@action
function action1()
endfunction

@action
function action2()
endfunction

@query
function query1()
endfunction

@query
function query2()
endfunction
"""


class ContractTests(unittest.TestCase):
    def test_dumps_and_loads(self):
        # create the contract
        owner = Entity()
        orig = Contract(CONTRACT_TEXT)
        orig.owner = owner

        # encode the contract
        encoded = orig.dumps()

        # re-create the contract
        new = Contract.loads(encoded)

        # checks
        self.assertIsInstance(new, Contract)
        self.assertEqual(orig.owner, new.owner)
        self.assertEqual(orig.digest, new.digest)
        self.assertEqual(orig.source, new.source)

    def test_dumps_and_loads_without_owner(self):
        # create the contract
        orig = Contract(CONTRACT_TEXT)

        # encode the contract
        encoded = orig.dumps()

        # re-create the contract
        new = Contract.loads(encoded)

        # checks
        self.assertIsInstance(new, Contract)
        self.assertEqual(orig.owner, new.owner)
        self.assertEqual(orig.digest, new.digest)
        self.assertEqual(orig.source, new.source)
