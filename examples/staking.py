import time

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.crypto import Entity, Address

HOST = '127.0.0.1'
PORT = 8000


def main():
    key_path = '/Users/nhutton/repos/ledger/build_debug/node1/p2p.key'

    with open(key_path, 'rb') as key_file:
        key_bytes = key_file.read()

    # create the entity from this private key
    entity = Entity(key_bytes)
    address = Address(entity)
    print('Address:', address)

    # create the APIs
    api = LedgerApi(HOST, PORT)

    # create the balance
    print('Submitting wealth creation...')
    api.sync(api.tokens.wealth(entity, 10000))

    print('Balance:', api.tokens.balance(entity))

    print('Stake..:', api.tokens.stake(entity))

    # submit and wait for the transfer to be complete
    print('Submitting stake request...')
    api.sync(api.tokens.add_stake(entity, 1000, 50))

    while True:

        print('Balance............:', api.tokens.balance(entity))
        print('Stake..............:', api.tokens.stake(entity))
        print('Stake on cooldown..:', api.tokens.stake_cooldown(entity))

        # De-stake half of the staked balance
        to_destake = int(api.tokens.stake(entity)/2)
        api.sync(api.tokens.de_stake(entity, to_destake, 500))

        # Collect cooled down stakes
        api.sync(api.tokens.collect_stake(entity, 500))
        time.sleep(1)


if __name__ == '__main__':
    main()
