#!/usr/bin/env python3
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

from fetch.ledger.crypto import Signing
from fetch.ledger.serialisation.objects import Tx
from fetch.ledger.serialisation.objects.transaction_api import create_transfer_tx, create_wealth_tx

from fetch.ledger.api.contracts import *
from fetch.ledger.api.common import ApiEndpoint

import base64
import binascii
import argparse
import os
import time
import random
import pprint

def parse_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', type=str, help='file to smart contract', default="./scripts/test.fetch")
    return parser.parse_args()

def main(index):

    args = parse_commandline()
    whole_file = open(args.filename, 'r').read()

    # We append some whitespace so each smart contract is 'unique'
    for i in range(index):
        whole_file += " "

    manager = SmartContractManager("localhost", "8000")

    contract_hash_b64 = manager.add_contract(whole_file)

    print("new contract. hash: " + contract_hash_b64)

    smart_contract = SmartContract("localhost", "8000", "PUBKEY1", contract_hash_b64)

    # These will be the only resources we allow setting/getting in our SC - note the second fn
    # in the smart contract example will fail for not locking counter2.
    resources = ["hello", "try", "this", "counter", "counter3"]
    fn_to_call = "main"

    # Keep trying to speculatively execute our contract until success
    while True:
        try:
            # Call main function speculatively to see what the result is
            speculative_output = smart_contract.run_speculative(resources, function_name=fn_to_call)
            print("Speculative output of calling {}: ".format(fn_to_call))
            pprint.pprint(speculative_output)
            break
        except Exception as ex:
            print(ex)
            print("Failed to submit speculatively. This might be as the submitted smart contract has not been mined yet. Retrying.")
            time.sleep(5)

    # run the sc X times
    invokations_wanted = 12
    for i in range(invokations_wanted):
        print("Submitting TX: {}".format(i))
        smart_contract.run(resources, function_name=fn_to_call)

    while True:
        speculative_output = smart_contract.run_speculative(resources, function_name=fn_to_call)
        print("Speculative output of N+1 times: ")
        pprint.pprint(speculative_output)

        if 'payload' in speculative_output and speculative_output['payload'][0] == 'The first counter is now: {}'.format(invokations_wanted):
            print("SUCCESS! Counter verified as correct")
            print()
            break
        else:
            time.sleep(5)

if __name__ == '__main__':
    for i in range(50):
        main(i)
