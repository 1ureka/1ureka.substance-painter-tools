import substance_painter as sp  # type: ignore
from randomize.utils import CollectResult
from randomize.handle_randomize import RandomizeHandler


def collect_from_layers(layers: list[object]) -> CollectResult:
    """
    從圖層列表中遞迴收集所有支援隨機化的來源物件。

    此函數會遞迴遍歷圖層列表，包括群組圖層的子圖層，並從每個圖層中收集:
    1. 圖層本身的來源 (透過 RandomizeHandler.collect_sources)
    2. 圖層的內容效果 (content_effects) 中的來源
    3. 圖層的遮罩效果 (mask_effects) 中的來源

    所有收集到的來源會合併到單一列表中返回。

    :param layers: Substance Painter 圖層物件的列表
    :type layers: list[object]
    :return: 收集到的來源物件列表，封裝在 CollectResult 中
    :rtype: CollectResult
    """
    sources: list[object] = []

    for layer in layers:
        is_group_layer = layer.get_type() == sp.layerstack.NodeType.GroupLayer

        if is_group_layer:
            collected = collect_from_layers(list(layer.sub_layers()))
            sources.extend(collected.sources)
        else:
            collected = RandomizeHandler.collect_sources(layer)
            sources.extend(collected.sources)

        if hasattr(layer, "content_effects") and layer.content_effects():
            for effect_layer in layer.content_effects():
                collected = RandomizeHandler.collect_sources(effect_layer)
                sources.extend(collected.sources)

        if hasattr(layer, "mask_effects") and layer.mask_effects():
            for effect_layer in layer.mask_effects():
                collected = RandomizeHandler.collect_sources(effect_layer)
                sources.extend(collected.sources)

    return CollectResult(sources=sources)


def main():
    """
    隨機化種子工具的主要入口函數。

    執行流程:
    1. 檢查是否有開啟的專案，若無則顯示警告並返回
    2. 遍歷專案中所有紋理集的所有堆疊
    3. 從每個堆疊的圖層中收集支援隨機化的來源物件
    4. 在 ScopedModification 上下文中批次處理所有來源
    5. 為所有來源設定相同的新隨機種子值
    6. 顯示處理結果，包括新種子值、成功和失敗數量

    此函數會處理整個專案中所有支援隨機化的 Substance 來源 (如程序紋理)
    並為它們設定相同的新隨機種子，以產生不同的隨機效果變化。

    使用 ScopedModification 確保所有修改作為單一操作記錄在
    Substance Painter 的 undo/redo 歷史中。

    :return: None
    """
    if not sp.project.is_open():
        return sp.logging.warning("未開啟任何專案，請先開啟一個專案。")

    sources: list[object] = []

    for texture_set in sp.textureset.all_texture_sets():
        texture_set_name = texture_set.name() or str(texture_set)

        try:
            for stack in list(texture_set.all_stacks()):
                layers = list(sp.layerstack.get_root_layer_nodes(stack))
                collected = collect_from_layers(layers)
                sources.extend(collected.sources)

        except Exception as e:
            sp.logging.error(f"收集紋理集 '{texture_set_name}' 的來源時發生錯誤: {str(e)}")

    if not sources:
        return sp.logging.warning("沒有找到可隨機化的來源")

    with sp.layerstack.ScopedModification("隨機化所有種子"):
        try:
            results = RandomizeHandler.process_sources(sources)
            new_seed, success_count, failed_count = results

            message = f"✓ 隨機化完成\n\n新的隨機種子: {new_seed}\n成功更新的來源數量: {success_count}\n失敗的來源數量: {failed_count}"
            sp.logging.info(message)

        except Exception as e:
            sp.logging.error(f"✗ 隨機化種子時發生錯誤: {str(e)}")
