import substance_painter as sp  # type: ignore
from typing import List, Dict, NamedTuple, Tuple, Type
from transform.utils import LayerHandler, ProcessArgs
from transform.handle_fill import FillLayerHandler
from transform.handle_generator import GeneratorLayerHandler
from ui.transform_select_dialog import ask_transform_settings


# UI 可以呈現成
# [status => 圖示] [完整圖層路徑]: [title]
# [detail]
class DispatchResult(NamedTuple):
    """
    圖層處理結果的命名元組，包含處理狀態、標題和詳細訊息。

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
圖層處理結果的字典型別別名。

鍵 (Tuple[str, ...]): 圖層的完整路徑，以元組表示，例如 ('紋理集名稱', '堆疊 0', '群組1', '圖層名稱')
值 (DispatchResult): 該圖層的處理結果

此資料結構用於儲存整個專案中所有已處理圖層的結果，便於後續統計和 UI 顯示。
"""


# 處理單一圖層
def dispatch_layer(layer: object, scale: float, rotation: float) -> DispatchResult:
    """
    處理單一圖層的縮放和旋轉變換。

    此函數會嘗試使用註冊的圖層處理器 (FillLayerHandler、GeneratorLayerHandler 等)
    來驗證和處理指定的圖層。處理流程為：
    1. 依序嘗試每個處理器驗證圖層
    2. 如果處理器跳過 (skipped) ，繼續嘗試下一個處理器
    3. 如果處理器拒絕 (rejected) ，返回失敗結果
    4. 如果處理器接受 (accepted) ，執行圖層處理並返回結果
    5. 若所有處理器都跳過，返回失敗結果

    :param layer: Substance Painter 的圖層物件，可能是 FillLayer、Effect 等類型
    :type layer: object
    :param scale: 縮放比例，例如 2.0 表示放大兩倍
    :type scale: float
    :param rotation: 旋轉角度 (度數)
    :type rotation: float
    :return: 圖層處理結果，包含成功/失敗狀態、標題和詳細訊息
    :rtype: DispatchResult
    """
    layer_name = str(layer.get_name())

    handlers: List[Type[LayerHandler]] = [
        FillLayerHandler,
        GeneratorLayerHandler,
    ]

    for handler in handlers:
        v_res = handler.validate_layer(layer)

        if v_res.status == "skipped":
            continue

        if v_res.status == "rejected":
            return DispatchResult.fail(f'圖層 "{layer_name}" 被 "{handler.__name__}" 拒絕處理', v_res.message)

        if v_res.status == "accepted":
            args = ProcessArgs(scale=scale, rotation=rotation)
            p_res = handler.process_layer(layer, args)

            if p_res.status == "success":
                return DispatchResult.success(f'圖層 "{layer_name}" 處理成功', p_res.message)
            elif p_res.status == "no_change":
                return DispatchResult.success(f'圖層 "{layer_name}" 無需修改', p_res.message)
            else:
                return DispatchResult.fail(f'圖層 "{layer_name}" 處理失敗', p_res.message)

    return DispatchResult.fail(f'圖層 "{layer_name}" 被跳過', "該圖層類型沒有適用的處理器")


# 遞迴處理圖層與群組圖層
def dispatch_layers(layers: List[object], base_path: List[str], scale: float, rotation: float) -> DispatchResults:
    """
    遞迴處理圖層列表，包括群組圖層及其子圖層。

    此函數會遍歷圖層列表，對每個圖層執行以下操作：
    1. 如果是群組圖層且不可見，跳過該群組及其所有子圖層
    2. 如果是群組圖層且可見，遞迴處理其子圖層
    3. 如果是一般圖層，調用 dispatch_layer 處理
    4. 處理圖層的 content_effects (內容效果)
    5. 處理圖層的 mask_effects (遮罩效果)

    所有處理結果會以圖層完整路徑為鍵，儲存在返回的字典中。

    :param layers: Substance Painter 圖層物件的列表
    :type layers: List[object]
    :param base_path: 當前圖層的基礎路徑，用於構建完整路徑，例如 ['紋理集1', '堆疊 0']
    :type base_path: List[str]
    :param scale: 縮放比例，例如 2.0 表示放大兩倍
    :type scale: float
    :param rotation: 旋轉角度 (度數) ，範圍 -180 到 180
    :type rotation: float
    :return: 圖層路徑到處理結果的映射字典
    :rtype: DispatchResults
    """
    results: DispatchResults = {}

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


def get_available_texture_sets() -> List[Tuple[str, bool]]:
    """
    獲取專案中所有可用的紋理集列表，並標記當前選中的紋理集。

    此函數會遍歷專案中的所有紋理集，並與當前啟用的紋理集進行比較，
    用於在 UI 中顯示紋理集選擇列表。

    :return: 紋理集資訊的列表，每個元素為 (紋理集名稱, 是否為當前選中) 的元組
    :rtype: List[Tuple[str, bool]]
    """
    texture_sets = []
    active_set = sp.textureset.get_active_stack().name() or str(sp.textureset.get_active_stack())

    for texture_set in sp.textureset.all_texture_sets():
        name = texture_set.name() or str(texture_set)
        is_selected = name == active_set
        texture_sets.append((name, is_selected))

    return texture_sets


def main() -> None:
    """
    映射變換工具的主要入口函數。

    執行流程：
    1. 檢查是否有開啟的專案，若無則顯示警告並返回
    2. 獲取所有可用的紋理集並顯示選擇對話框
    3. 讓使用者選擇要處理的紋理集以及設定縮放和旋轉參數
    4. 在 ScopedModification 上下文中批次處理選定的紋理集
    5. 對每個紋理集的所有堆疊執行圖層變換
    6. 收集所有處理結果並顯示結果對話框 (TODO)

    此函數使用 ScopedModification 確保所有修改作為單一操作記錄在
    Substance Painter 的 undo/redo 歷史中。

    :return: None
    """
    if not sp.project.is_open():
        return sp.logging.warning("未開啟任何專案，請先開啟一個專案。")

    # ------ 讓使用者選擇紋理集 ------
    rows = [{"name": name, "selected": is_selected} for name, is_selected in get_available_texture_sets()]

    if not rows:
        return sp.logging.warning("沒有紋理集可供選擇。")

    result = ask_transform_settings(rows)

    if result is None:
        return sp.logging.info("使用者已取消操作。")

    # ------ 邏輯處理 ------
    with sp.layerstack.ScopedModification("映射變換"):
        all_results: DispatchResults = {}

        for texture_set in sp.textureset.all_texture_sets():
            texture_set_name = texture_set.name() or str(texture_set)

            if texture_set_name not in result["texture_sets"]:
                continue

            try:
                for index, stack in enumerate(texture_set.all_stacks()):
                    results = dispatch_layers(
                        layers=list(sp.layerstack.get_root_layer_nodes(stack)),
                        base_path=[texture_set_name, f"堆疊 {index}"],
                        scale=result["scale"],
                        rotation=result["rotation"],
                    )

                    all_results.update(results)

            except Exception as e:
                sp.logging.error(f"處理紋理集 {texture_set_name} 時發生錯誤: {str(e)}")

    # ------ 顯示結果 ------
    # TODO
