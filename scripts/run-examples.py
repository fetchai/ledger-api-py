#!/usr/bin/env python3
import argparse
import logging

from fetch.ledger.examples import SimpleBalanceRequest, SimpleTransferExchange

TEST_CASES = (
    ('balance request', SimpleBalanceRequest),
    ('balance transfer', SimpleTransferExchange),
)


def parse_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='The host name to perform the checks on')
    parser.add_argument('-p', '--port', default=8000, type=int, help='The port number to connect to')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    return parser.parse_args()


def main():
    args = parse_commandline()

    # configure the logging level
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level)

    # run all the tests
    for name, klass in TEST_CASES:
        logging.info('Running Test: {}'.format(name))

        # create and
        try:
            test_instance = klass(args.host, args.port)
            test_instance.run()

            logging.debug('Running Test: {} (complete)'.format(name))

        except RuntimeError as ex:
            logging.exception('Error running test')


if __name__ == '__main__':
    main()
