import binascii
import io
import ecdsa
import hashlib

def to_hex(value):
    return binascii.hexlify(value).decode()

def parse_integer(stream: io.BytesIO):
    header = stream.read(1)[0]
    if (header & 0x80) == 0:
        return header & 0x7F
    else:
        type = (header & 0x60) >> 5
        if type == 3:
            return -(header & 0x1f)
        elif type == 2:
            signed_flag = bool(header & 0x10)
            log2_value_length = header & 0x0F
            value_length = 1 << log2_value_length

            # print('Debug', signed_flag, log2_value_length, format(header, 'b'), '{:0x}'.format(header))

            value = 0
            for n in range(value_length):
                byte_value = int(stream.read(1)[0])
                shift = (value_length - (n + 1)) * 8

                # print('- {} -> {:0x}'.format(n, byte_value))

                byte_value <<= shift
                value |= byte_value

            if signed_flag:
                value = -value

            # print('Final: ', value)

            return value


def parse_address(stream: io.BytesIO):
    return binascii.hexlify(stream.read(32)).decode()


def parse_bytes(stream: io.BytesIO):
    length = parse_integer(stream)

    # print('Bytes Len:', length)

    return stream.read(length)


def parse_public_key(stream: io.BytesIO):
    identifer = stream.read(1)

    if identifer[0] == 0x04:
        payload = stream.read(64)
    elif identifer[0] == 0x03 or identifer[0] == 0x02:
        payload = stream.read(32)
    else:
        assert False

    return binascii.hexlify(identifer + payload).decode()


def main():

    raw = binascii.unhexlify(
        'a12180532398dd883d1990f7dad3fde6a53a53347afc2680a04748f7f15ad03cadc4d464c0c8c103e8c2000f424041eaab0b666f6f2e6261722e62617a066c61756e6368000418c2a33af8bd2cba7fa714a840a308a217aa4483880b1ef14b4fdffe08ab956e3f4b921cec33be7c258cfd7025a2b9a942770e5b17758bcc4961bbdc75a0251c')
    stream = io.BytesIO(raw)

    magic = stream.read(1)[0]
    assert magic == 0xa1

    header = stream.read(2)

    # parse the header types
    version = (header[0] & 0xE0) >> 5
    charge_unit_flag = bool((header[0] & 0x08) >> 3)
    transfer_flag = bool((header[0] & 0x04) >> 2)
    multiple_transfers_flag = bool((header[0] & 0x02) >> 1)
    valid_from_flag = bool((header[0] & 0x01))

    contract_type = (header[1] & 0xC0) >> 6
    signature_count_minus1 = (header[1] & 0x3F)

    num_signatures = signature_count_minus1 + 1

    from_address = parse_address(stream)

    print('version.................:', version)
    print('charge_unit_flag........:', charge_unit_flag)
    print('transfer_flag...........:', transfer_flag)
    print('multiple_transfers_flag.:', multiple_transfers_flag)
    print('valid_from_flag.........:', valid_from_flag)
    print('contract_type...........:', contract_type)
    print('signature_count_minus1..:', signature_count_minus1)
    print('from....................:', from_address)

    if transfer_flag:
        transfer_count = 1

        if multiple_transfers_flag:
            transfer_count = parse_integer(stream) + 2

        print('num transfers...........:', transfer_count)

        for n in range(transfer_count):
            to = parse_address(stream)
            amount = parse_integer(stream)

            print(' >=> from: {} to: {} amount: {}'.format(from_address, to, amount))

    if valid_from_flag:
        print('valid from..............:', parse_integer(stream))

    print('valid until.............:', parse_integer(stream))
    print('charge rate.............:', parse_integer(stream))
    if charge_unit_flag:
        print('charge unit.............:', parse_integer(stream))
    print('charge limit............:', parse_integer(stream))

    if contract_type != 0:
        contract_header = int(stream.read(1)[0])

        wildcard = bool(contract_header & 0x80)

        if wildcard:
            shard_mask = format(1, 'b')
        else:

            extended_shard_mask_flag = bool(contract_header & 0x40)

            if not extended_shard_mask_flag:
                mask = 0xf if contract_header & 0x10 else 0x3
                shard_mask = format(contract_header & mask, 'b')

            else:
                bit_length = 1 << ((contract_header & 0x3F) + 3)
                byte_length = bit_length // 8
                print('Shard Length: ###', bit_length, byte_length)
                shard_bytes = stream.read(byte_length)
                shard_mask = ''
                for b in shard_bytes:
                    shard_mask += format(b, 'b')

        print('shard mask..............:', shard_mask)

        if contract_type == 1:
            contract_digest = parse_address(stream)
            contract_address = parse_address(stream)

            print('contract digest.........:', contract_digest)
            print('contract address........:', contract_address)

        elif contract_type == 2:
            chain_code = parse_bytes(stream).decode()

            print('chain code..............:', chain_code)

        else:
            assert False

        action = parse_bytes(stream).decode()
        # data = binascii.hexlify(parse_bytes(stream)).decode()
        data = parse_bytes(stream)

        print('action..................:', action)
        print('data....................:', data)

    if signature_count_minus1 == 0x3F:
        additional_signatures = parse_integer(stream)

        print('additional signatures...:', additional_signatures)

        num_signatures += additional_signatures

    print('num signatures..........:', num_signatures)

    print('identities..............:')
    public_keys = []
    for n in range(num_signatures):
        public_key = parse_public_key(stream)
        public_keys.append(public_key)

        print(' - {:2} -> {}'.format(n, public_key))

    payload_end = stream.tell()

    print('signatures..............:')
    for n in range(num_signatures):
        sig = parse_bytes(stream)

        curve = ecdsa.SECP256k1
        digest = hashlib.sha256

        key = ecdsa.VerifyingKey.from_string(binascii.unhexlify(public_keys[n])[1:], curve=curve, hashfunc=digest)
        verified = key.verify(sig, raw[:payload_end], hashfunc=digest)

        status = ' Valid ' if verified else 'INVALID'
        print(' - {:2} -> {} -> {}'.format(n, status, to_hex(sig)))


    # for test generation
    payload = binascii.hexlify(raw[:payload_end]).decode()
    print('Payload:', payload)



if __name__ == '__main__':
    main()
