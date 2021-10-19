
from typing import NamedTuple

import rlp

from wvm_keys import keys
from wvm_keys import datatypes
from wvm_keys.exceptions import (
    BadSignature,
)

from wvm_utils import (
    int_to_big_endian,
    ValidationError,
)

from wvm.abc import (
    SignedTransactionAPI,
    UnsignedTransactionAPI,
)
from wvm.constants import (
    CREATE_CONTRACT_ADDRESS,
)
from wvm.typing import (
    Address,
    VRS,
)
from wvm._utils.numeric import (
    is_even,
)

from wvm.rlp.transactions import BaseTransaction

##?

def extract_transaction_sender(transaction: SignedTransactionAPI) -> Address:
    vrs = (transaction.y_parity, transaction.r, transaction.s)
    signature = keys.Signature(vrs=vrs)
    message = transaction.get_message_for_signing()
    public_key = signature.recover_public_key_from_msg(message)
    sender = public_key.to_canonical_address()
    return Address(sender)


class IntrinsicGasSchedule(NamedTuple):
    gas_tx: int
    gas_txcreate: int
    gas_txdatazero: int
    gas_txdatanonzero: int


def calculate_intrinsic_gas(
        gas_schedule: IntrinsicGasSchedule,
        transaction: SignedTransactionAPI,
) -> int:
    num_zero_bytes = transaction.data.count(b'\x00')
    num_non_zero_bytes = len(transaction.data) - num_zero_bytes
    if transaction.to == CREATE_CONTRACT_ADDRESS:
        create_cost = gas_schedule.gas_txcreate
    else:
        create_cost = 0
    return (
        gas_schedule.gas_tx
        + num_zero_bytes * gas_schedule.gas_txdatazero
        + num_non_zero_bytes * gas_schedule.gas_txdatanonzero
        + create_cost
    )
