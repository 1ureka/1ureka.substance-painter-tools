import substance_painter as sp  # type: ignore
from typing import List, Dict ,NamedTuple, Tuple, Type
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

# 處理單一圖層
def dispatch_layer(layer: object, scale: float, rotation: float) -> DispatchResult:
    layer_name = str(layer.get_name())

    handlers: List[Type[LayerHandler]] = [
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

# 遞迴處理圖層與群組圖層
def dispatch_layers(layers: List[object], base_path: List[str], scale: float, rotation: float) -> Dict[Tuple[str], DispatchResult]:
    results: Dict[Tuple[str], DispatchResult] = {}

    for layer in layers:
        is_group_layer = layer.get_type() == sp.layerstack.NodeType.GroupLayer
        layer_name = str(layer.get_name())
        current_path = tuple(base_path + [layer_name])

        if is_group_layer and not layer.is_visible():
            title = f'圖層 "{layer_name}" 被跳過'
            detail = f'群組圖層 "{layer_name}" 未顯示，其本身與內部圖層皆跳過處理'

            result = DispatchResult.fail(title, detail)
            results[current_path] = result
            continue

        if is_group_layer:
            results.update(dispatch_layers(list(layer.sub_layers()), list(current_path), scale, rotation))
        else:
            results[current_path] = dispatch_layer(layer, scale, rotation)

        if hasattr(layer, "content_effects") and layer.content_effects():
            for effect_layer in layer.content_effects():
                effect_path = current_path + (f"{effect_layer.get_name()} (效果)",)
                results[effect_path] = dispatch_layer(effect_layer, scale, rotation)

        if hasattr(layer, "mask_effects") and layer.mask_effects():
            for effect_layer in layer.mask_effects():
                mask_path = current_path + (f"{effect_layer.get_name()} (遮罩)",)
                results[mask_path] = dispatch_layer(effect_layer, scale, rotation)

    return results

# 入口函式， TODO: 應該是完整流程，包括運作前檢查、呼叫UI 等等
def main() -> None:
    pass
