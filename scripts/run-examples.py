#!/usr/bin/env python3
import argparse
import fnmatch
import os
import shutil
import subprocess
import sys
import time

import requests

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
GENESIS_PATH = os.path.join(PROJECT_ROOT, 'genesis.json')
WORKING_PATH = os.path.join(PROJECT_ROOT, '.ledger')
EXAMPLES_FOLDER = os.path.join(PROJECT_ROOT, 'examples')
EXAMPLES_BLACK_LIST = (
    'crypto_prediction_model.py',
    'staking.py',
    'governance.py',
    'synergetic.py',
    'introduction.py',
)


def parse_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('constellation', type=os.path.abspath,
                        help='The path to the constellation executable to check against')
    return parser.parse_args()


def _wait_for_chain_height(height: int):
    time.sleep(10)  # allow the ledger to start up first

    s = requests.session()

    for n in range(30):
        r = s.get('http://127.0.0.1:8000/api/status/chain?size=1')
        if not (200 <= r.status_code < 300):
            raise RuntimeError('Failed to query the chain status')

        r = r.json()
        if r['chain'][0]['blockNumber'] >= height:
            return

        # wait for a bit
        time.sleep(1)

    raise RuntimeError('Ledger instance failed to launch')


def run_example(args, example_path: str) -> bool:
    print('==================================================================================================')
    print('= Running: {}'.format(os.path.relpath(example_path, EXAMPLES_FOLDER)))
    print('==================================================================================================')

    ledger_cmd = [
        args.constellation,
        '-standalone',
        '-block-interval', '2000',
        '-genesis-file-location', GENESIS_PATH,
    ]

    # make sure the workspace is okay
    if os.path.exists(WORKING_PATH):
        shutil.rmtree(WORKING_PATH)
    os.makedirs(WORKING_PATH)

    success = False
    with open(os.path.join(WORKING_PATH, 'node.log'), 'w') as log_path:
        try:
            print('Starting ledger instance...')

            # start the ledger instance in the background
            ledger_process = subprocess.Popen(ledger_cmd, cwd=WORKING_PATH, stdout=log_path, stderr=subprocess.STDOUT)

            print('Starting ledger instance...waiting for block generation')

            # wait to make sure that the chain height
            _wait_for_chain_height(2)

            print('Starting ledger instance...complete')

            # run the example code
            subprocess.check_call(["python3", example_path])

            print('\n\n STATUS: OKAY')

            # signal it was a success
            success = True

        except Exception:
            print('\n\n STATUS: FAILED')
        finally:
            ledger_process.kill()
            ledger_process.wait()
            pass

    print('\n\n--------------------------------------------------------------------------------------------------\n\n')

    return success


def main():
    args = parse_commandline()

    success = False
    for root, _, files in os.walk(EXAMPLES_FOLDER):
        for filename in fnmatch.filter(files, '*.py'):
            abs_path = os.path.abspath(os.path.join(root, filename))
            rel_path = os.path.relpath(abs_path, EXAMPLES_FOLDER)

            # skip black listed examples
            if rel_path in EXAMPLES_BLACK_LIST:
                continue

            # run the example
            if not run_example(args, abs_path):
                print('Example: {} failed'.format(rel_path))
                break

    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
