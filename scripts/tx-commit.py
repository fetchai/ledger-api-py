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

from fetchai.ledger.api import submit_json_transaction

import argparse
import sys
import json


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Commits transaction in wire format to node")

    parser.add_argument('-H', '--host-name', type=str,
                        help='Host name of the node where transaction is supposed to be committed. The hostname is in following format `host[:port]`, for example `localhost:8000`, where `:port` fraction is not madatory and defaults to `:8000` if not provided.',
                        default="localhost:8000")

    v_group = parser.add_mutually_exclusive_group(required=True)
    v_group.add_argument('-t', '--tx-wire-format-string', type=str,
                         help='Transaction in wire format, for example -t \'{"ver":"1.0", "data":"..."}\'.')
    v_group.add_argument('-f', '--filename', type=str, help='Filename containing transaction in wire format.')
    v_group.add_argument('-c', '--from-stdin', action='store_true', help='Read wire tx from stdin.')

    return parser.parse_args(args)


def main():
    args = parse_args()

    host_name_fragments = args.host_name.split(":")
    host = host_name_fragments[0]
    port = host_name_fragments[1] if len(host_name_fragments) > 1 else "8000"

    if args.tx_wire_format_string:
        wire_tx = args.tx_wire_format_string
    elif args.filename:
        with open(args.filename, 'r') as f:
            wire_tx = f.read()
    elif args.from_stdin:
        wire_tx = sys.stdin.read()
    else:
        # should not get into this case
        assert False

    wire_tx_dic = json.loads(wire_tx)
    # submit the transaction
    submit_json_transaction(host, port, wire_tx_dic)


if __name__ == '__main__':
    main()
