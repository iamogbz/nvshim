# pylint: skip-file
from typing import (
    Callable,
    TypeVar,
)

ReturnType = TypeVar("ReturnType")

def fixture(func: Callable[..., ReturnType]) -> Callable[..., ReturnType]: ...
