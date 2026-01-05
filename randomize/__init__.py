import substance_painter as sp  # type: ignore
from randomize.utils import CollectResult
from randomize.handle_randomize import RandomizeHandler


def collect_from_layers(layers: list[object]) -> CollectResult:
    """?"""
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
    """?"""
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
