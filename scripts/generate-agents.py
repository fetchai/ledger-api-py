#!/usr/bin/env python3
import argparse
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from fetch.ledger.examples import MultipleBalanceRequest

def parse_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='The host name to perform the checks on')
    parser.add_argument('-p', '--port', default=8000, type=int, help='The port number to connect to')
    parser.add_argument('-t', '--transactions', default=3, type=int, help='Number of transactions to do')
    parser.add_argument('-x', '--threads', default=4, type=int, help='Number of threads to use')
    parser.add_argument('-v', '--verbose', default=True, type=bool, help='Verbose output or not')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    return parser.parse_args()


def multithreading(func, args, workers):
    with ThreadPoolExecutor(workers) as ex:
        res = ex.map(func, args)

    return list(res)

def main():
    args = parse_commandline()

    # configure the logging level
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level)

    bulk_req = MultipleBalanceRequest(args.host, args.port)
    bulk_req.run(args.transactions)

    # Verify the transactions exist, but not too fast so as not to overwhelm the http server
    multithreading(lambda a : a.update(), bulk_req.accounts, args.threads)

    if args.verbose:
        print("Created accounts:")
        for account in bulk_req.accounts:
            print(account)
        print("")
        print("Transfer 99:")


    # Transfer some amount from half of the accounts to the others
    for index in range(len(bulk_req.accounts) // 2):
        account1 = bulk_req.accounts[2*index]
        account2 = bulk_req.accounts[(2*index)-1]

        account1.send_funds(99, account2)
        if(args.verbose):
            print(account1)
            print(account2)

    # Check balances
    if args.verbose:
        while True:
            print("See if accounts still 'settle' after a short while")
            #time.sleep(20)

            print("Final account balances:")
            for account in bulk_req.accounts:
                account.update(expect_new_balance = False)
                print(account)

            dummy = input("press key to check again")

if __name__ == '__main__':
    main()
