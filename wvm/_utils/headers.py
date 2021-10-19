
import datetime
from typing import (
    Dict,
    Tuple,
)

from wvm_typing import (
    Address,
)

from wvm.abc import BlockHeaderAPI
from wvm.constants import (
    BLANK_ROOT_HASH,
    GENESIS_BLOCK_NUMBER,
    GENESIS_PARENT_HASH,
    ZERO_ADDRESS,
)
from wvm.typing import (
    BlockNumber,
    HeaderParams,
)


def wvm_now() -> int:
    """
    The timestamp is in UTC.
    """
    return int(datetime.datetime.utcnow().timestamp())


def new_timestamp_from_parent(parent: BlockHeaderAPI) -> int:
    """
    Generate a timestamp to use on a new header.
    Generally, attempt to use the current time. If timestamp is too old (equal
    or less than parent), return `parent.timestamp + 1`. If parent is None,
    then consider this a genesis block.
    """
    if parent is None:
        return wvm_now()
    else:
        # header timestamps must increment
        return max(
            parent.timestamp + 1,
            wvm_now(),
        )


def fill_header_params_from_parent(
        parent: BlockHeaderAPI,
        difficulty: int,
        timestamp: int,
        coinbase: Address = ZERO_ADDRESS,
        nonce: bytes = None,
        extra_data: bytes = None,
        transaction_root: bytes = None,
        state_root: bytes = None,
        mix_hash: bytes = None,
        receipt_root: bytes = None) -> Dict[str, HeaderParams]:

    if parent is None:
        parent_hash = GENESIS_PARENT_HASH
        block_number = GENESIS_BLOCK_NUMBER
        if state_root is None:
            state_root = BLANK_ROOT_HASH
    else:
        parent_hash = parent.hash
        block_number = BlockNumber(parent.block_number + 1)

        if state_root is None:
            state_root = parent.state_root

    header_kwargs: Dict[str, HeaderParams] = {
        'parent_hash': parent_hash,
        'coinbase': coinbase,
        'state_root': state_root,
        'difficulty': difficulty,
        'block_number': block_number,
        'timestamp': timestamp,
    }
    if nonce is not None:
        header_kwargs['nonce'] = nonce
    if extra_data is not None:
        header_kwargs['extra_data'] = extra_data
    if transaction_root is not None:
        header_kwargs['transaction_root'] = transaction_root
    if receipt_root is not None:
        header_kwargs['receipt_root'] = receipt_root
    if mix_hash is not None:
        header_kwargs['mix_hash'] = mix_hash

    return header_kwargs


