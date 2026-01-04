from typing import Dict, NamedTuple, Tuple, Literal, Protocol


class ValidationResult(NamedTuple):
    """
    圖層驗證結果的命名元組。

    用於封裝圖層處理器對圖層的驗證結果，決定該圖層是否應該被處理。
    驗證結果有三種狀態:
    - accepted: 圖層符合處理條件，可以被處理
    - skipped: 圖層不屬於該處理器的處理範圍，應由下一個處理器驗證
    - rejected: 圖層屬於該處理器的範圍但不應該被處理 (例如錨點圖層、專案資源等)

    Attributes:
        status (Literal["accepted", "skipped", "rejected"]): 驗證狀態
        message (str): 驗證訊息，說明驗證結果的原因
    """

    status: Literal["accepted", "skipped", "rejected"]
    message: str

    @classmethod
    def ok(cls):
        """
        建立一個接受的驗證結果。
        """
        return cls("accepted", "OK")

    @classmethod
    def skip(cls, reason="不屬於該圖層類型"):
        """
        建立一個跳過的驗證結果。
        """
        return cls("skipped", reason)

    @classmethod
    def reject(cls, reason="不該處理的圖層"):
        """
        建立一個拒絕的驗證結果。
        """
        return cls("rejected", reason)


class ProcessResult(NamedTuple):
    """
    圖層處理結果的命名元組。

    用於封裝圖層處理器對圖層執行變換操作後的結果，包含處理狀態和詳細訊息。
    處理結果有三種狀態:
    - success: 處理成功，圖層的參數已被修改
    - failure: 處理失敗，發生錯誤導致無法完成處理
    - no_change: 處理完成但無需修改，圖層沒有可調整的參數

    Attributes:
        status (Literal["success", "failure", "no_change"]): 處理狀態
        message (str): 處理訊息，說明處理結果的詳細內容或錯誤原因
    """

    status: Literal["success", "failure", "no_change"]
    message: str

    @classmethod
    def success(cls, message="處理成功"):
        """
        建立一個成功的處理結果。

        :param message: 成功訊息，通常包含參數變更的詳細內容
        """
        return cls("success", message)

    @classmethod
    def fail(cls, message="處理失敗"):
        """
        建立一個失敗的處理結果。
        """
        return cls("failure", message)

    @classmethod
    def no_change(cls):
        """
        建立一個無需修改的處理結果。
        """
        return cls("no_change", "圖層無需修改，沒有需要調整的參數")


class ProcessArgs(NamedTuple):
    """
    封裝傳遞給圖層處理器的變換參數，包含縮放比例和旋轉角度。
    """

    scale: float
    rotation: float


class LayerHandler(Protocol):
    """
    圖層處理器的協定 (Protocol) 介面。

    定義所有圖層處理器必須實作的方法，包括驗證圖層和處理圖層兩個靜態方法。
    處理器採用策略模式，每個處理器負責特定類型的圖層 (如填充圖層、生成器圖層等) 。

    處理流程:
    1. validate_layer: 檢查圖層是否符合處理條件
    2. process_layer: 對符合條件的圖層執行變換操作

    實作此協定的類別應該提供這兩個靜態方法，以便於統一的圖層處理流程。
    """

    @staticmethod
    def validate_layer(layer: object) -> ValidationResult: ...

    @staticmethod
    def process_layer(layer: object, args: ProcessArgs) -> ProcessResult: ...


class DispatchResult(NamedTuple):
    """
    經過所有圖層處理器的處理結果命名元組，包含處理狀態、標題和詳細訊息。

    用於封裝單一圖層或效果圖層的處理結果，提供成功或失敗的狀態資訊。
    這個結果會被用於 UI 顯示，透過樹狀結構呈現給使用者。

    Attributes:
        status (bool): 處理狀態， True 表示成功， False 表示失敗
        title (str): 簡短的處理結果標題，例如「圖層 'Fill 1' 處理成功」
        detail (str): 詳細的處理訊息，例如參數變更內容或錯誤原因
    """

    status: bool
    title: str
    detail: str

    @classmethod
    def success(cls, title: str, detail: str):
        return cls(True, title, detail)

    @classmethod
    def fail(cls, title: str, detail: str):
        return cls(False, title, detail)


DispatchResults = Dict[Tuple[str, ...], DispatchResult]
"""
- 鍵 (Tuple[str, ...]): 圖層的完整路徑，以元組表示，例如 ('紋理集名稱', '堆疊 0', '群組1', '圖層名稱')
- 值 (DispatchResult): 該圖層經過所有圖層處理器的處理結果

此資料結構用於儲存整個專案中所有已處理圖層的結果，便於後續統計和 UI 顯示。
"""
