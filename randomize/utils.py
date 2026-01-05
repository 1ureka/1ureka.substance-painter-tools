from typing import NamedTuple, Protocol


class CollectResult(NamedTuple):
    """
    來源收集結果的命名元組。

    用於封裝從圖層或圖層列表中收集到的支援隨機化的來源物件。
    每個來源都是 Substance Painter 的 Substance 來源物件，
    包含 $randomseed 參數可以被隨機化處理。

    Attributes:
        sources (list[object]): 收集到的來源物件列表
    """

    sources: list[object]


class ProcessResult(NamedTuple):
    """
    隨機化處理結果的命名元組。

    用於封裝批次處理多個來源後的結果，包含生成的隨機種子、
    成功設定的來源數量以及失敗的來源數量。

    這些資訊用於向使用者顯示隨機化操作的執行狀況。

    Attributes:
        new_seed (int): 生成的新隨機種子值
        success_count (int): 成功設定的來源數量
        failed_count (int): 失敗的來源數量
    """

    new_seed: int
    success_count: int
    failed_count: int


class Handler(Protocol):
    """
    隨機化處理器的協定 (Protocol) 介面。

    定義所有隨機化處理器必須實作的方法，包括收集來源和處理來源兩個靜態方法。

    處理流程:
    1. collect_sources: 從圖層中收集支援隨機化的來源
    2. process_sources: 為收集到的來源設定新的隨機種子

    實作此協定的類別應該提供這兩個靜態方法，以便於統一的隨機化處理流程。
    """

    @staticmethod
    def collect_sources(layer: object) -> CollectResult: ...

    @staticmethod
    def process_sources(sources: list[object]) -> ProcessResult: ...
