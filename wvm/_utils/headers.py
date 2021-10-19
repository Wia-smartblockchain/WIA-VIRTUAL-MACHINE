
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
    LIX_LIMIT_EMA_DENOMINATOR,
    LIX_LIMIT_ADJUSTMENT_FACTOR,
    LIX_LIMIT_MAXIMUM,
    LIX_LIMIT_MINIMUM,
    LIX_LIMIT_USAGE_ADJUSTMENT_NUMERATOR,
    LIX_LIMIT_USAGE_ADJUSTMENT_DENOMINATOR,
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
        lix_limit: int,
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
        'lix_limit': gas_limit,
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


def compute_lix_limit_bounds(previous_limit: int) -> Tuple[int, int]:
    """
    Compute the boundaries for the block gas limit based on the parent block.
    """
    boundary_range = previous_limit // LIX_LIMIT_ADJUSTMENT_FACTOR

    # the boundary range is the exclusive limit, therefore the inclusive bounds are
    # (boundary_range - 1) and (boundary_range + 1) for upper and lower bounds, respectively
    upper_bound_inclusive = min(LIX_LIMIT_MAXIMUM, previous_limit + boundary_range - 1)
    lower_bound_inclusive = max(LIX_LIMIT_MINIMUM, previous_limit - boundary_range + 1)
    return lower_bound_inclusive, upper_bound_inclusive

#?
def compute_lix_limit(parent_header: BlockHeaderAPI, genesis_lix_limit: int) -> int:
    """
    A simple strategy for adjusting the lix limit.
    For each block:
    - decrease by 1/1024th of the lix limit from the previous block
    - increase by 50% of the total lix used by the previous block
    If the value is less than the given `genesis_lix_limit`:
    - increase the lix limit by 1/1024th of the lix limit from the previous block.
    If the value is less than the LIX_LIMIT_MINIMUM:
    - use the LIX_LIMIT_MINIMUM as the new gas limit.
    """
    if genesis_gas_limit < LIX_LIMIT_MINIMUM:
        raise ValueError(
            "The `genesis_lix_limit` value must be greater than the "
            f"GAS_LIMIT_MINIMUM.  Got {genesis_gas_limit}.  Must be greater than "
            f"{GAS_LIMIT_MINIMUM}"
        )

    if parent_header is None:
        return genesis_gas_limit

    decay = parent_header.gas_limit // GAS_LIMIT_EMA_DENOMINATOR

    if parent_header.gas_used:
        usage_increase = (
            parent_header.gas_used * GAS_LIMIT_USAGE_ADJUSTMENT_NUMERATOR
        ) // (
            GAS_LIMIT_USAGE_ADJUSTMENT_DENOMINATOR
        ) // (
            GAS_LIMIT_EMA_DENOMINATOR
        )
    else:
        usage_increase = 0

    gas_limit = max(
        GAS_LIMIT_MINIMUM,
        # + 1 because the decay is an exclusive limit we have to remain inside of
        (parent_header.gas_limit - decay + 1) + usage_increase
    )

    if gas_limit < GAS_LIMIT_MINIMUM:
        return GAS_LIMIT_MINIMUM
    elif gas_limit < genesis_gas_limit:
        # - 1 because the decay is an exclusive limit we have to remain inside of
        return parent_header.gas_limit + decay - 1
    else:
        return gas_limit  
