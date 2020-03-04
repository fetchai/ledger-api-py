import base64
import os

from fetchai.ledger.api import LedgerApi, TokenApi, ContractsApi, TransactionApi
from fetchai.ledger.crypto import Address, Identity, Entity

PASSWORD = 'Password!12345'
ADDRESS = 'dTSCNwHBPoDdESpxj6NQkPDvX3DN1DFKGsUPZNVWDVDrfur4z'
ENCRYPTED_KEY_FP = os.path.join(os.path.dirname(__file__), 'private-key.key')


def main():
    # *************************************
    # ***** Working with Private Keys *****
    # *************************************

    # Create a new (random) private key by instantiating an entity object
    entity = Entity()

    # Return the private key as a hexadecimal string
    private_key_hex = entity.private_key_hex

    print('\nThe new private key in hexadecimal is:', private_key_hex)

    # Return the private key in bytes
    private_key_bytes = entity.private_key_bytes

    # Get the public key associated with the private key of an Entity object
    print('\nThe associated public key in hexadecimal is: ', entity.public_key_hex)

    # Construct an Entity from bytes
    entity2 = Entity(private_key_bytes)

    # Construct an entity from a private key stored as a base64 string
    entity3 = entity.from_base64(base64.b64encode(private_key_bytes).decode())

    assert entity.private_key_hex == entity3.private_key_hex, 'Private keys should match\n'

    # *************************************
    # ***** Serializing Private Keys ******
    # *************************************

    # serialize to JSON with AES
    serialized = entity.dumps(PASSWORD)

    print('\nThis serializes to the the following encrypted JSON string :\n', serialized)

    # Re-create an entity from an encrypted JSON string
    entity4 = entity.loads(serialized, PASSWORD)

    print('\nWhich can be de-serialized to an entity containing the following hex private key:',
          entity4.private_key_hex)

    # Check if a password is strong enough to be accepted by our serialization functionality.
    # A password must contain 14 chars or more, with one or more uppercase, lowercase, numeric and a one or more special char
    strong = 'is strong enough' if Entity.is_strong_password(PASSWORD) else 'is not strong enough'
    print(
        '\nOur example password: {} upon testing {} to be used with our serialization functionality\n'.format(PASSWORD,
                                                                                                              strong))

    # We can also encrypt a password from the terminal using our prompt functionality.
    with open(ENCRYPTED_KEY_FP, 'w') as private_key_file:
        entity.prompt_dump(private_key_file)
        private_key_file.close()

    print("\nSuccess! Private key, encrypted with the password has been saved in examples.")
    print("\nUse the same password as just before to reload the entity saved in file\n")

    # Load private key from the terminal using our prompt functionality.
    with open(ENCRYPTED_KEY_FP, 'r') as private_key_file:
        loaded_entity = entity.prompt_load(private_key_file)

    if loaded_entity.public_key_hex == entity.public_key_hex:
        print('\nLoaded public/private key pair match, saved in file: ' + ENCRYPTED_KEY_FP)

    # *************************************
    # ***** Working with Public keys ******
    # *************************************

    # Identity represents only a public key; where an entity objects represent a public/private key pair
    identity = Identity(entity)

    # Obtain public key as a string encoded in hexadecimal
    public_key_hex = identity.public_key_hex

    # Obtain public key as a string encoded in base64
    public_key_base64 = identity.public_key

    # Obtain public key as a Buffer in Nodejs or a Uint8Array in the browser
    public_key_bytes = identity.public_key_bytes

    # Construct an identity from a hexadecimal-encoded public key
    ident2 = identity.from_hex(public_key_hex)

    # Construct an identity from a public key in base64 form
    ident3 = identity.from_base64(public_key_base64)

    print('An Identity object represents a public key\n')

    # Construct an identity from bytes
    ident4 = Identity(public_key_bytes)

    # *************************************
    # ****** Working with Addresses *******
    # *************************************

    # Construct an address from an entity object
    address = Address(entity)

    # Construct an Address from a base58-encoded string: the public representation of an Address
    address2 = Address(ADDRESS)

    # Validate that a string is a valid address (verify checksum, valid base58-encoding and length)
    valid_address = 'is valid.' if Address.is_address(ADDRESS) else 'is not valid.'
    print('The Address generated from our entity {}'.format(valid_address))

    # We can get the base 58 value of an address from an address object as follows:
    public_address = str(address)

    print('\nThe public base58 representation of this Address is:', public_address)

    # *************************************
    # ****** Working with a Ledger ********
    # *************************************

    host = '127.0.0.1'
    port = 8000

    # The LedgerApi class has some general methods for working with the Ledger and
    # builds and holds references to various subclasses which encompass different functions to be performed against
    # against a Ledger Nodes public API.
    # See the Bootstrap examples file for further details relating to finding a Host and Port of an available
    print("\nTrying to connect to a Ledger Node...")

    api = LedgerApi(host, port)

    print("\nConnected to Ledger Node at Host: {} and Port {} ...".format(host, port))

    # The TokenApi Class has methods for staking in our Proof-of-stake model, checking the
    # balance of an account, and performing transfers of funds between accounts.

    # See the staking example file in this folder for further details.
    assert isinstance(api.tokens, TokenApi), "token property should be instance of TokenApi class"

    # We can get the nodes current block number
    block_number = api.tokens.current_block_number()
    print("\nThe current block number of the Ledger is:", block_number)

    # ContractsApi allows contract submition, and for contracts to be called on them
    # See the contracts example file in this folder for further details.
    assert isinstance(api.contracts, ContractsApi), "contracts property should be instance of ContractsApi"

    # TransactionApi contains methods to query the status of a submitted transaction
    # See the tx example file in this folder for further details.
    # TODO add tx example file, then delete this comment.
    assert isinstance(api.tx, TransactionApi), "tx property should be instance of TransactionApi"


if __name__ == '__main__':
    main()
