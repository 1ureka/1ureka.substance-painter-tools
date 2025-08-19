import substance_painter as sp  # type: ignore
from PySide2 import QtWidgets  # type: ignore

from typing import Optional
import importlib
import ui.texture_sets_select as texture_sets_select

importlib.reload(texture_sets_select)

# -------------------------------------------------------------------------
# 工具函數
# -------------------------------------------------------------------------


def log_info(*messages):
    for message in messages:
        print(message)
    print("-")


def is_split_layer(layer) -> bool:
    return hasattr(layer, "source_mode") and layer.source_mode == sp.source.SourceMode.Split


class TransformApplier:
    scale = 1.0
    rotation = 0

    @staticmethod
    def fill_source(layer, info: str) -> None:
        modif_params = layer.get_projection_parameters()

        if TransformApplier.scale != 1.0:
            current_scale = modif_params.uv_transformation.scale
            new_scale = [scale * TransformApplier.scale for scale in current_scale]
            modif_params.uv_transformation.scale = new_scale

        if TransformApplier.rotation != 0:
            current_rotation = modif_params.uv_transformation.rotation
            new_rotation = (current_rotation + TransformApplier.rotation) % 360
            modif_params.uv_transformation.rotation = new_rotation

        if TransformApplier.scale != 1.0 or TransformApplier.rotation != 0:
            old_params = layer.get_projection_parameters()
            layer.set_projection_parameters(modif_params)
            new_params = layer.get_projection_parameters()
            log_info(
                f"{info}",
                f">>> 縮放: <{old_params.uv_transformation.scale} => {new_params.uv_transformation.scale}>",
                f">>> 旋轉: <{old_params.uv_transformation.rotation} => {new_params.uv_transformation.rotation}>",
            )

    @staticmethod
    def generator_source(layer, info: str) -> None:
        modif_params = layer.get_source().get_parameters().items()

        # TODO: 實現生成器映射變換
        log_info(f"{info}", "生成器映射變換尚未實現，跳過")


class TransformChecker:
    @staticmethod
    def _material_source(layer) -> tuple[bool, str]:
        if hasattr(layer.get_material_source(), "anchor"):
            return (False, "來源為 Anchor")

        return (True, "")

    @staticmethod
    def fill_source(layer, channel_name: Optional[str] = None) -> tuple[bool, str]:
        modes = [sp.layerstack.ProjectionMode.UV, sp.layerstack.ProjectionMode.Triplanar]
        if layer.get_projection_mode() not in modes:
            return (False, "不是使用 UV 或 Triplanar 映射")

        if layer.source_mode == sp.source.SourceMode.Material:
            return TransformChecker._material_source(layer)

        source = layer.get_source(channel_name) if channel_name else layer.get_source()

        if source is None:
            return (False, "來源為 None")

        if hasattr(source, "resource_id") and "project" in source.resource_id.context:
            return (False, "來源為 Project Resource, 很有可能為烘焙結果而非紋理")

        if hasattr(source, "anchor"):
            return (False, "來源為 Anchor")

        if hasattr(source, "get_parameters"):
            procedural_params = ["scale", "tile", "tiling", "pattern_scale"]
            if any(param in source.get_parameters() for param in procedural_params) and "3D" in layer.get_name():
                return (False, "來源為 Procedural")

        return (True, "")

    @staticmethod
    def generator_source(layer) -> tuple[bool, str]:
        source = layer.get_source()
        if not source:
            return (False, "來源為 None")

        keys = [key.lower() for key in source.get_parameters().keys()]
        required_keywords = ["scale", "ao", "curvature", "position"]
        missing = [kw for kw in required_keywords if not any(kw in key for key in keys)]

        if missing:
            return (False, f"缺少必要參數: {', '.join(missing)}")

        return (True, "")


# -------------------------------------------------------------------------
# 主要函數
# -------------------------------------------------------------------------


def process_fill_layer(layer, name: str) -> None:
    if is_split_layer(layer):
        results = [TransformChecker.fill_source(layer, channel) for channel in layer.active_channels]
        if all(result[0] for result in results):
            TransformApplier.fill_source(layer, f"✅ {name} 是可變換的 Split Layer")
        else:
            reasons = ", ".join(reason for ok, reason in results if not ok)
            log_info(f"❌ {name} 是不可變換的 Split Layer（{reasons}），跳過處理")

    else:
        ok, reason = TransformChecker.fill_source(layer)
        if ok:
            TransformApplier.fill_source(layer, f"✅ {name} 是可變換的 Single Layer")
        else:
            log_info(f"❌ {name} 是不可變換的 Single Layer（{reason}），跳過處理")


def process_generator_layer(layer, name: str) -> None:
    ok, reason = TransformChecker.generator_source(layer)
    if ok:
        TransformApplier.generator_source(layer, f"✅ {name} 是可變換的 Generator")
    else:
        log_info(f"❌ {name} 是不可變換的 Generator（{reason}），跳過處理")


def process_layer_effects(layer, name: str) -> None:
    if hasattr(layer, "content_effects") and layer.content_effects():
        for effect in layer.content_effects():
            process_layer_recursive(effect, f"{name} / ContentEffects")

    if hasattr(layer, "mask_effects") and layer.mask_effects():
        for effect in layer.mask_effects():
            process_layer_recursive(effect, f"{name} / MaskEffects")


def process_layer_recursive(layer, layer_path: str = ""):
    layer_name = layer.get_name()
    layer_type = layer.get_type()
    full_path = f"{layer_path} / {layer_name}" if layer_path else layer_name

    group_type = sp.layerstack.NodeType.GroupLayer
    generator_type = sp.layerstack.NodeType.GeneratorEffect
    fill_types = [sp.layerstack.NodeType.FillLayer, sp.layerstack.NodeType.FillEffect]
    paint_type = sp.layerstack.NodeType.PaintLayer

    if layer_type == group_type:
        if not layer.is_visible():
            return log_info(f"❌ {full_path} 是不可見的 Group Layer，跳過處理其所有子圖層")

        for sub_layer in list(layer.sub_layers()):
            process_layer_recursive(sub_layer, full_path)
        process_layer_effects(layer, full_path)

    elif layer_type == generator_type:
        process_generator_layer(layer, full_path)

    elif layer_type in fill_types:
        process_fill_layer(layer, full_path)
        process_layer_effects(layer, full_path)

    elif layer_type == paint_type:
        process_layer_effects(layer, full_path)

    else:
        log_info(f"❌ {full_path} 是 {layer_type}，跳過處理")


# -------------------------------------------------------------------------
# 主流程
# -------------------------------------------------------------------------


def main():
    # ------ 準備對話框所需資料 ------
    if not sp.project.is_open():
        return sp.logging.warning("未開啟任何專案，請先開啟一個專案。")

    rows = [texture_sets_select.Row(texture_set.name()) for texture_set in sp.textureset.all_texture_sets()]

    if not rows:
        return sp.logging.warning("沒有紋理集可供選擇。")

    # ------ 對話框流程 ------
    result = None
    dialog: Optional[texture_sets_select.Dialog] = None

    try:
        dialog = texture_sets_select.Dialog(rows, sp.ui.get_main_window())

        if not dialog.exec_() == QtWidgets.QDialog.Accepted:
            return sp.logging.info("取消映射操作")

        if not dialog.result or not dialog.result.texture_sets:
            return sp.logging.info("取消映射操作，未選擇任何紋理集")

        result = dialog.result

    except Exception as e:
        return sp.logging.info(f"❌ 處理對話框時發生錯誤: {e}")

    finally:
        if dialog:
            dialog.deleteLater()

    # ------ 邏輯處理 ------
    TransformApplier.scale = result.scale
    TransformApplier.rotation = result.rotation

    with sp.layerstack.ScopedModification("映射變換"):
        for texture_set in sp.textureset.all_texture_sets():
            set_name = texture_set.name()
            set_stacks = texture_set.all_stacks()

            if set_name not in result.texture_sets:
                continue

            try:
                log_info(f"🎨 處理 Texture Set: {set_name}")
                for index, stack in enumerate(set_stacks):
                    for layer in sp.layerstack.get_root_layer_nodes(stack):
                        process_layer_recursive(layer, f"{set_name} / Stack{index}")

            except Exception as e:
                log_info(f"❌ 處理 Texture Set 時發生錯誤: {e}")

    sp.logging.info("映射調整完成")
