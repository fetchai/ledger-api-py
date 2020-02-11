from fetchai.ledger.api import LedgerApi
from fetchai.ledger.crypto import Entity, Address

HOST = '127.0.0.1'
PORT = 8000


def main():
    api = LedgerApi(HOST, PORT)
    # in our examples we use Addresses with funds, which we load from hex-encoded private keys.
    identity1 = Entity.from_hex('6e8339a0c6d51fc58b4365bf2ce18ff2698d2b8c40bb13fcef7e1ba05df18e4b')
    identity2 = Entity.from_hex('e833c747ee0aeae29e6823e7c825d3001638bc30ffe50363f8adf2693c3286f8')

    # we make a Transfer which returns a transaction id.
    tx = api.tokens.transfer(identity1, identity2, 2500, 20)

    # wait for the transaction to complete so that the information is 100% present
    api.sync(tx)

    # we Verify that the transaction is the submitted transaction is the sent transaction
    # TxContents object (below contents variable) contains all properties sent to ledger in transaction API call
    contents = api.tx.contents(tx)

    # below we access a subset of the properties of our TxContents object
    valid_until = contents.valid_until
    valid_from = contents.valid_from
    from_address = contents.from_address
    transfers = contents.transfers

    # iterate over the transfers in the transaction, which is singular in this instance
    for to_address, amount in transfers.items():
        print(
            "\nThe submitted transaction is from Address: {}\nto Address: {} \nof amount: {}\nand is valid from (block number): {} \nand valid until (block number): {}".format(
                str(from_address), to_address, amount, valid_from, valid_until))

    nonexistent_entity = Entity()

    # check the amount being transferred to a particular address; zero in the below instance
    amount = contents.transfers_to(nonexistent_entity)

    if amount == 0:
        print("\nAs expected, nothing is being transferred to Address: ", str(Address(nonexistent_entity)))
    else:
        print("\nExample failure: nothing should be transferred to Address: ", str(Address(nonexistent_entity)))

    # check the status of a transaction. This is an alternative to calling the LedgerApi's sync method, which itself polls the below status endpoint
    status = api.tx.status(tx)

    print('\nCurrent Status is :', status.status)


if __name__ == '__main__':
    main()
