from typing import NamedTuple, Protocol


class CollectResult(NamedTuple):
    """收集來源結果"""

    sources: list[object]


class ProcessResult(NamedTuple):
    """處理結果"""

    new_seed: int
    success_count: int
    failed_count: int


class Handler(Protocol):
    """隨機化處理器協定"""

    @staticmethod
    def collect_sources(layer: object) -> CollectResult: ...

    @staticmethod
    def process_sources(sources: list[object]) -> ProcessResult: ...
