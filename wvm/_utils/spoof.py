
from typing import (
    Any,
    TypeVar,
    Union,
)

from wvm_utils.toolz import (
    merge,
)

from wvm.constants import (
    DEFAULT_SPOOF_Y_PARITY,
    DEFAULT_SPOOF_R,
    DEFAULT_SPOOF_S,
)

from wvm.abc import (
    SignedTransactionAPI,
    UnsignedTransactionAPI,
)

SPOOF_ATTRIBUTES_DEFAULTS = {
    'y_parity': DEFAULT_SPOOF_Y_PARITY,
    'r': DEFAULT_SPOOF_R,
    's': DEFAULT_SPOOF_S
}

T = TypeVar('T', bound='SpoofAttributes')


class SpoofAttributes:
    def __init__(
            self,
            spoof_target: Union[SignedTransactionAPI, UnsignedTransactionAPI],
            **overrides: Any) -> None:
        self.spoof_target = spoof_target
        self.overrides = overrides

        if 'from_' in overrides:
            if hasattr(spoof_target, 'sender'):
                raise TypeError(
                    "A from_ parameter can only be supplied when the spoof target",
                    "does not have a sender attribute.  SpoofTransaction will not attempt",
                    "to override the sender of a signed transaction.")

            overrides['sender'] = overrides['from_']
            overrides['get_sender'] = lambda: overrides['from_']
            for attr, value in SPOOF_ATTRIBUTES_DEFAULTS.items():
                if not hasattr(spoof_target, attr):
                    overrides[attr] = value

    def __getattr__(self, attr: str) -> Any:
        if attr in self.overrides:
            return self.overrides[attr]
        else:
            return getattr(self.spoof_target, attr)

    def copy(self: T, **kwargs: Any) -> T:
        new_target = self.spoof_target.copy(**kwargs)
        new_overrides = merge(self.overrides, kwargs)
        return type(self)(new_target, **new_overrides)
