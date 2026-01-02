import substance_painter as sp  # type: ignore
from typing import List, NamedTuple
from transform.utils import LayerHandler, ProcessArgs
from transform.handle_fill import FillLayerHandler
from transform.handle_generator import GeneratorLayerHandler

# UI 可以呈現成
# [status => 圖示] [完整圖層路徑]: [title]
# [detail]
class DispatchResult(NamedTuple):
    status: bool
    title: str
    detail: str

    @classmethod
    def success(cls, title: str, detail: str):
        return cls(True, title, detail)

    @classmethod
    def fail(cls, title: str, detail: str):
        return cls(False, title, detail)

def dispatch_layer(layer: object, scale: float, rotation: float) -> DispatchResult:
    layer_name = str(layer.get_name())

    handlers: List[LayerHandler] = [
        FillLayerHandler,
        GeneratorLayerHandler,
    ]

    for handler in handlers:
        v_res = handler.validate_layer(layer)

        if v_res.status == 'skipped':
            continue

        if v_res.status == 'rejected':
            return DispatchResult.fail(f'圖層 "{layer_name}" 被 "{handler.__name__}" 拒絕處理', v_res.message)

        if v_res.status == 'accepted':
            args = ProcessArgs(scale=scale, rotation=rotation)
            p_res = handler.process_layer(layer, args)

            if p_res.status == 'success':
                return DispatchResult.success(f'圖層 "{layer_name}" 處理成功', p_res.message)
            elif p_res.status == 'no_change':
                return DispatchResult.success(f'圖層 "{layer_name}" 無需修改', p_res.message)
            else:
                return DispatchResult.fail(f'圖層 "{layer_name}" 處理失敗', p_res.message)

    return DispatchResult.fail(f'圖層 "{layer_name}" 被跳過', '該圖層類型沒有適用的處理器')

def dispatch_layers(layers: List[object], scale: float, rotation: float) -> List[DispatchResult]:
    results: List[DispatchResult] = []

    for layer in layers:
        is_group_layer = layer.get_type() == sp.layerstack.NodeType.GroupLayer
        layer_name = str(layer.get_name())

        if is_group_layer and not layer.is_visible():
            result = DispatchResult.fail(f'圖層 "{layer_name}" 被跳過', f'群組圖層 "{layer_name}" 未顯示，其本身與內部圖層皆跳過處理')
            results.append(result)
            continue

        if is_group_layer:
            results.extend(dispatch_layers(list(layer.sub_layers()), scale, rotation))
        else:
            results.append(dispatch_layer(layer, scale, rotation))

        if hasattr(layer, "content_effects") and layer.content_effects():
            for effect in layer.content_effects():
                results.append(dispatch_layer(effect, scale, rotation))

        if hasattr(layer, "mask_effects") and layer.mask_effects():
            for effect in layer.mask_effects():
                results.append(dispatch_layer(effect, scale, rotation))

    return results
