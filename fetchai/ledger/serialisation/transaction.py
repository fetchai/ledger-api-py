import io
from typing import List

from fetchai.ledger.bitvector import BitVector
from fetchai.ledger.crypto import Entity
from fetchai.ledger.transaction import Transaction
from . import address, integer, bytearray, identity

MAGIC = 0xA1
VERSION = 1

NO_CONTRACT = 0
SMART_CONTRACT = 1
CHAIN_CODE = 2
SYNERGETIC = 3


def _log2(value: int) -> int:
    count = 0
    while value > 1:
        value >>= 1
        count += 1
    return count


def _byte(value: int) -> bytes:
    return bytes([value])


def _map_contract_mode(payload: Transaction):
    if payload.synergetic_data_submission:
        return SYNERGETIC

    if payload.action:
        if payload.chain_code:
            return CHAIN_CODE
        assert payload.contract_digest is not None

        return SMART_CONTRACT
    else:
        return NO_CONTRACT


def encode_payload(buffer: io.BytesIO, payload: Transaction):
    num_transfers = len(payload.transfers)
    num_signatures = len(payload.signers)

    # sanity check
    assert num_signatures >= 1

    num_extra_signatures = num_signatures - 0x40 if num_signatures > 0x40 else 0
    signalled_signatures = num_signatures - (num_extra_signatures + 1)
    has_valid_from = payload.valid_from != 0

    header0 = VERSION << 5
    header0 |= (1 if num_transfers > 0 else 0) << 2
    header0 |= (1 if num_transfers > 1 else 0) << 1
    header0 |= 1 if has_valid_from else 0

    # determine the node of the contract
    contract_mode = _map_contract_mode(payload)

    header1 = contract_mode << 6
    header1 |= signalled_signatures & 0x3f

    buffer.write(bytes([MAGIC, header0, header1]))

    address.encode(buffer, payload.from_address)
    if num_transfers > 1:
        integer.encode(buffer, num_transfers - 2)

    for destination, amount in payload.transfers.items():
        address.encode(buffer, destination)
        integer.encode(buffer, amount)

    if has_valid_from:
        integer.encode(buffer, payload.valid_from)

    integer.encode(buffer, payload.valid_until)
    integer.encode(buffer, payload.charge_rate)
    integer.encode(buffer, payload.charge_limit)

    if NO_CONTRACT != contract_mode:

        shard_mask_length = len(payload.shard_mask)

        if shard_mask_length <= 1:

            # signal this is a wildcard transaction (expensive!!!)
            buffer.write(_byte(0x80))

        else:

            shard_mask_bytes = bytes(payload.shard_mask)
            log2_mask_length = _log2(shard_mask_length)

            if shard_mask_length < 8:
                assert len(shard_mask_bytes) == 1

                contract_header = shard_mask_bytes[0] & 0xF
                if log2_mask_length == 2:
                    contract_header |= 0x10

                # write the mask to the stream
                buffer.write(_byte(contract_header))

            else:

                assert shard_mask_length <= 512

                contract_header = 0x40 | ((log2_mask_length - 3) & 0x3f)

                buffer.write(_byte(contract_header))
                buffer.write(shard_mask_bytes)

        if SMART_CONTRACT == contract_mode or SYNERGETIC == contract_mode:
            address.encode(buffer, payload.contract_digest)
            address.encode(buffer, payload.contract_address)
        elif CHAIN_CODE == contract_mode:
            encoded_chain_code = payload.chain_code.encode('ascii')
            bytearray.encode(buffer, encoded_chain_code)
        else:
            assert False

        # write the action and data fields
        encoded_action = payload.action.encode('ascii')
        bytearray.encode(buffer, encoded_action)
        bytearray.encode(buffer, payload.data)

    if num_extra_signatures > 0:
        integer.encode(buffer, num_extra_signatures)

    # write all the signers public keys
    for signer in payload.signers.keys():
        identity.encode(buffer, signer)


def encode_transaction(payload: Transaction, signers: List[Entity]):
    # encode the contents of the transaction
    buffer = io.BytesIO()
    encode_payload(buffer, payload)

    # extract the payload buffer
    payload_bytes = buffer.getvalue()

    # append all the signatures of the signers in order
    for signer in payload.signers.keys():
        if signer not in signers:
            raise RuntimeError('Missing signer signing set')

        # find the index to the appropriate index and lookup the entity
        entity = signers[signers.index(signer)]

        # sign the payload contents and add it to the buffer
        bytearray.encode(buffer, entity.sign(payload_bytes))

    # return the encoded transaction
    return buffer.getvalue()


def decode_transaction(stream: io.BytesIO) -> (bool, Transaction):
    # ensure the at the magic is correctly configured
    magic = stream.read(1)[0]
    if magic != MAGIC:
        raise RuntimeError('Unable to parse transaction from stream, invalid magic')

    # extract the header bytes
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

    # ensure that the version is correct
    if version != VERSION:
        raise RuntimeError('Unable to parse transaction from stream, incompatible version')

    tx = Transaction()

    # decode the address from the thread
    tx.from_address = address.decode(stream)

    if transfer_flag:

        # determine the number of transfers that are present in the transaction
        if multiple_transfers_flag:
            transfer_count = integer.decode(stream) + 2
        else:
            transfer_count = 1

        for n in range(transfer_count):
            to = address.decode(stream)
            amount = integer.decode(stream)

            tx.add_transfer(to, amount)

    if valid_from_flag:
        tx.valid_from = integer.decode(stream)

    tx.valid_until = integer.decode(stream)
    tx.charge_rate = integer.decode(stream)

    assert not charge_unit_flag, "Currently the charge unit field is not supported"

    tx.charge_limit = integer.decode(stream)

    if contract_type != NO_CONTRACT:
        contract_header = int(stream.read(1)[0])

        wildcard = bool(contract_header & 0x80)

        shard_mask = BitVector()
        if not wildcard:
            extended_shard_mask_flag = bool(contract_header & 0x40)

            if not extended_shard_mask_flag:

                if contract_header & 0x10:
                    mask = 0xf
                    bit_size = 4
                else:
                    mask = 0x3
                    bit_size = 2

                # extract the shard mask from the header
                shard_mask = BitVector.from_bytes(bytes([contract_header & mask]), bit_size)

            else:
                bit_length = 1 << ((contract_header & 0x3F) + 3)
                byte_length = bit_length // 8

                assert (bit_length % 8) == 0  # this should be enforced as part of the spec

                # extract the mask from the next N bytes
                shard_mask = BitVector.from_bytes(stream.read(byte_length), bit_length)

        if contract_type == SMART_CONTRACT or contract_type == SYNERGETIC:
            contract_digest = address.decode(stream)
            contract_address = address.decode(stream)

            tx.target_contract(contract_digest, contract_address, shard_mask)

        elif contract_type == CHAIN_CODE:
            encoded_chain_code_name = bytearray.decode(stream)

            tx.target_chain_code(encoded_chain_code_name.decode('ascii'), shard_mask)

        else:
            # this is mostly a guard against a desync between this function and `_map_contract_mode`
            raise RuntimeError("Unhandled contract type")

        tx.action = bytearray.decode(stream).decode('ascii')
        tx.data = bytearray.decode(stream)

    if signature_count_minus1 == 0x3F:
        additional_signatures = integer.decode(stream)
        num_signatures += additional_signatures

    # extract all the signing public keys from the stream
    public_keys = [identity.decode(stream) for _ in range(num_signatures)]

    # extract full copy of the payload
    payload_bytes = stream.getvalue()[:stream.tell()]

    verified = []
    for ident in public_keys:
        # for n in range(num_signatures):

        # extract the signature from the stream
        signature = bytearray.decode(stream)

        # verify if this signature is correct
        verified.append(ident.verify(payload_bytes, signature))

        # build a metadata object to store in the tx
        tx._signers[ident] = {
            'signature': signature,
            'verified': verified[-1],
        }

    return all(verified), tx
