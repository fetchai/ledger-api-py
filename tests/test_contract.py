import unittest

from fetchai.ledger.contract import SmartContract
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


class SmartContractTests(unittest.TestCase):
    def test_dumps_and_loads(self):
        # create the contract
        owner = Entity()
        orig = SmartContract(CONTRACT_TEXT)
        orig.owner = owner

        # encode the contract
        encoded = orig.dumps()

        # re-create the contract
        new = SmartContract.loads(encoded)

        # checks
        self.assertIsInstance(new, SmartContract)
        self.assertEqual(orig.owner, new.owner)
        self.assertEqual(orig.digest, new.digest)
        self.assertEqual(orig.source, new.source)

    def test_dumps_and_loads_without_owner(self):
        # create the contract
        orig = SmartContract(CONTRACT_TEXT)

        # encode the contract
        encoded = orig.dumps()

        # re-create the contract
        new = SmartContract.loads(encoded)

        # checks
        self.assertIsInstance(new, SmartContract)
        self.assertEqual(orig.owner, new.owner)
        self.assertEqual(orig.digest, new.digest)
        self.assertEqual(orig.source, new.source)
