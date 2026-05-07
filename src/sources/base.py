from typing import Iterator, Protocol, runtime_checkable

from src.models import RawProspect


@runtime_checkable
class SourceAdapter(Protocol):
    """Yield RawProspect records from an external source.

    Adapters must be idempotent: running twice produces no duplicates
    (dedupe is the DB layer's responsibility, but adapters should not
    intentionally yield the same logical prospect twice within one run).
    """

    name: str

    def fetch(self, **kwargs) -> Iterator[RawProspect]:
        ...
