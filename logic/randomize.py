import substance_painter as sp
import random


# -------------------------------------------------------------------------
# 工具函數
# -------------------------------------------------------------------------


def log_info(*messages):
    for message in messages:
        print(message)
    print("-")


def get_source_mode(source):
    """取得來源模式"""
    try:
        return source.source_mode
    except:
        return None


def check_for_random_seed(current_source, sources):
    """檢查來源是否包含隨機種子參數"""
    if type(current_source) == sp.source.SourceSubstance:
        parameters = current_source.get_parameters()

        # 檢查 Substance 是否有隨機種子
        if "$randomseed" in parameters:
            sources.append(current_source)

        # 檢查 Substance 的輸入是否也有其他包含隨機種子的 Substance
        for name in current_source.image_inputs:
            input_source = current_source.get_source(name)
            check_for_random_seed(input_source, sources)


def find_sources(node, sources):
    """從節點中尋找包含隨機種子的來源"""
    valid_node_types = (
        sp.layerstack.NodeType.FillLayer,
        sp.layerstack.NodeType.FillEffect,
        sp.layerstack.NodeType.FilterEffect,
        sp.layerstack.NodeType.GeneratorEffect,
    )

    if node.get_type() in valid_node_types:
        source_list = []
        mode = get_source_mode(node)

        if mode == sp.source.SourceMode.Material:
            source_list.append(node.get_material_source())

        elif mode == sp.source.SourceMode.Split:
            for channel in node.active_channels:
                source_list.append(node.get_source(channel))

        else:
            source_list.append(node.get_source())

        for current_source in source_list:
            check_for_random_seed(current_source, sources)


def iterate_layer(parent, sources):
    """遞迴遍歷圖層以尋找隨機種子來源"""
    if parent.get_type() == sp.layerstack.NodeType.FillLayer:
        find_sources(parent, sources)

    # 處理圖層效果
    layer_types_with_effects = (
        sp.layerstack.NodeType.FillLayer,
        sp.layerstack.NodeType.GroupLayer,
        sp.layerstack.NodeType.PaintLayer,
    )

    if parent.get_type() in layer_types_with_effects:
        # 內容效果
        if hasattr(parent, "content_effects") and parent.content_effects():
            for effect in parent.content_effects():
                find_sources(effect, sources)

        # 遮罩效果
        if hasattr(parent, "mask_effects") and parent.mask_effects():
            for effect in parent.mask_effects():
                find_sources(effect, sources)

    # 遞迴處理群組圖層的子圖層
    if parent.get_type() == sp.layerstack.NodeType.GroupLayer:
        for layer in parent.sub_layers():
            iterate_layer(layer, sources)


# -------------------------------------------------------------------------
# 主要函數
# -------------------------------------------------------------------------


def main():
    """隨機化所有種子的主函數"""
    if not sp.project.is_open():
        return sp.logging.warning("未開啟任何專案，請先開啟一個專案。")

    log_info("🎲 開始隨機化所有種子...")

    # 來源列表
    sources = []

    try:
        # 遍歷所有紋理集和堆疊以收集資源
        for texture_set in sp.textureset.all_texture_sets():
            set_name = texture_set.name()
            log_info(f"🎨 處理 Texture Set: {set_name}")

            for stack_index, stack in enumerate(texture_set.all_stacks()):
                for layer in sp.layerstack.get_root_layer_nodes(stack):
                    iterate_layer(layer, sources)

        if not sources:
            return sp.logging.warning("沒有找到可隨機化的種子")

        log_info(f"✅ 找到 {len(sources)} 個包含隨機種子的來源")

        # 設定隨機種子參數
        parameters = {"$randomseed": random.getrandbits(16)}
        log_info(f"🔢 新的隨機種子值: {parameters['$randomseed']}")

        # 批次處理
        with sp.layerstack.ScopedModification("隨機化所有種子"):
            for i, source in enumerate(sources):
                try:
                    source.set_parameters(parameters)
                    log_info(f"✅ 已更新來源 {i + 1}/{len(sources)}")
                except Exception as e:
                    log_info(f"❌ 更新來源 {i + 1} 時發生錯誤: {e}")

        sp.logging.info("種子隨機化完成")

    except Exception as e:
        error_msg = f"隨機化種子時發生錯誤: {e}"
        log_info(f"❌ {error_msg}")
        sp.logging.error(error_msg)
