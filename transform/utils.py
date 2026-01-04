from typing import NamedTuple, Literal, Protocol


# accepted 代表可以處理， skipped 代表不屬於此類型(給下一個 handler 驗證)， rejected 代表屬於此類型但應該跳過(不處理)
class ValidationResult(NamedTuple):
    status: Literal["accepted", "skipped", "rejected"]
    message: str

    @classmethod
    def ok(cls):
        return cls("accepted", "OK")

    @classmethod
    def skip(cls, reason="不屬於該圖層類型"):
        return cls("skipped", reason)

    @classmethod
    def reject(cls, reason="不該處理的圖層"):
        return cls("rejected", reason)


class ProcessResult(NamedTuple):
    status: Literal["success", "failure", "no_change"]
    message: str

    @classmethod
    def success(cls, message="處理成功"):
        return cls("success", message)

    @classmethod
    def fail(cls, message="處理失敗"):
        return cls("failure", message)

    @classmethod
    def no_change(cls):
        return cls("no_change", "圖層無需修改，沒有需要調整的參數")


class ProcessArgs(NamedTuple):
    scale: float
    rotation: float


class LayerHandler(Protocol):
    @staticmethod
    def validate_layer(layer: object) -> ValidationResult: ...
    @staticmethod
    def process_layer(layer: object, args: ProcessArgs) -> ProcessResult: ...
