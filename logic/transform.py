import substance_painter as sp  # type: ignore
from PySide2 import QtWidgets  # type: ignore

# from my_plugins import log_info
from typing import Optional
import importlib
import ui.texture_sets_select as texture_sets_select

importlib.reload(texture_sets_select)

SCALE = 1.5
ROTATION = 0

# -------------------------------------------------------------------------
# 工具函數
# -------------------------------------------------------------------------


def log_info(*messages):
    for message in messages:
        print(message)
    print("-")


def apply_transform(layer, info: str) -> None:
    modif_params = layer.get_projection_parameters()

    if SCALE != 1.0:
        current_scale = modif_params.uv_transformation.scale
        new_scale = [scale * SCALE for scale in current_scale]
        modif_params.uv_transformation.scale = new_scale

    if ROTATION != 0:
        current_rotation = modif_params.uv_transformation.rotation
        new_rotation = (current_rotation + ROTATION) % 360
        modif_params.uv_transformation.rotation = new_rotation

    if SCALE != 1.0 or ROTATION != 0:
        old_params = layer.get_projection_parameters()
        layer.set_projection_parameters(modif_params)
        new_params = layer.get_projection_parameters()
        log_info(
            f"{info}",
            f">>> 縮放: <{old_params.uv_transformation.scale} => {new_params.uv_transformation.scale}>",
            f">>> 旋轉: <{old_params.uv_transformation.rotation} => {new_params.uv_transformation.rotation}>",
        )


def is_split_layer(layer) -> bool:
    return hasattr(layer, "source_mode") and layer.source_mode == sp.source.SourceMode.Split


def is_source_scalable(layer, channel_name: Optional[str] = None) -> tuple[bool, str]:
    # --- Material Source ---

    if layer.source_mode == sp.source.SourceMode.Material:
        # 若來源是 anchor，則不變換
        if hasattr(layer.get_material_source(), "anchor"):
            return (False, "來源為 Anchor")

        return (True, "")

    # --- Other Source ---

    source = layer.get_source(channel_name) if channel_name else layer.get_source()

    # 若沒來源則不變換
    if source is None:
        return (False, "來源為 None")

    # 若來源為 anchor，則不變換
    if hasattr(source, "anchor"):
        return (False, "來源為 Anchor")

    # 若為 procedural source，則不變換
    if hasattr(source, "get_parameters"):
        procedural_params = ["scale", "tile", "tiling", "pattern_scale"]
        if any(param in source.get_parameters() for param in procedural_params) and "3D" in layer.get_name():
            return (False, "來源為 Procedural")

    return (True, "")


# -------------------------------------------------------------------------
# 主要函數
# -------------------------------------------------------------------------


def process_layer(layer, name: str) -> None:
    # 檢查圖層類型是否為 FillLayer 或 FillEffect
    types = [sp.layerstack.NodeType.FillLayer, sp.layerstack.NodeType.FillEffect]
    if layer.get_type() not in types:
        return log_info(f"❌ {name} 不是 FillLayer 或 FillEffect，跳過處理")

    # 檢查圖層的 projection mode 是否為 UV 或 Triplanar
    modes = [sp.layerstack.ProjectionMode.UV, sp.layerstack.ProjectionMode.Triplanar]
    if layer.get_projection_mode() not in modes:
        return log_info(f"❌ {name} 不是使用 UV 或 Triplanar，跳過處理")

    # split source
    if is_split_layer(layer):
        results = [is_source_scalable(layer, channel) for channel in layer.active_channels]
        if all(result[0] for result in results):
            apply_transform(layer, f"✅ {name} 是可縮放的 Split Layer")
        else:
            reasons = ", ".join(reason for ok, reason in results if not ok)
            log_info(f"❌ {name} 是不可縮放的 Split Layer（{reasons}），跳過處理")

    # single source
    else:
        ok, reason = is_source_scalable(layer)
        if ok:
            apply_transform(layer, f"✅ {name} 是可縮放的 Single Layer")
        else:
            log_info(f"❌ {name} 是不可縮放的 Single Layer（{reason}），跳過處理")


def process_layer_effects(layer, name: str) -> None:
    if hasattr(layer, "content_effects") and layer.content_effects():
        for effect in layer.content_effects():
            process_layer(effect, f"{name} / ContentEffects / {effect.get_name()}")

    if hasattr(layer, "mask_effects") and layer.mask_effects():
        for effect in layer.mask_effects():
            process_layer(effect, f"{name} / MaskEffects / {effect.get_name()}")


def process_layer_recursive(layer, layer_path: str = ""):
    layer_name = layer.get_name()
    full_path = f"{layer_path} / {layer_name}" if layer_path else layer_name

    if layer.get_type() == sp.layerstack.NodeType.GroupLayer:
        for sub_layer in list(layer.sub_layers()):
            process_layer_recursive(sub_layer, full_path)
        process_layer_effects(layer, full_path)
    else:
        process_layer(layer, full_path)
        process_layer_effects(layer, full_path)


# -------------------------------------------------------------------------
# 主流程
# -------------------------------------------------------------------------


def main():
    if not sp.project.is_open():
        return sp.logging.warning("未開啟任何專案，請先開啟一個專案。")

    rows = [texture_sets_select.Row(texture_set.name()) for texture_set in sp.textureset.all_texture_sets()]

    if not rows:
        return sp.logging.warning("沒有紋理集可供選擇。")

    dialog = texture_sets_select.Dialog(rows, sp.ui.get_main_window())

    try:
        if (not dialog.exec_() == QtWidgets.QDialog.Accepted) or (not dialog.result):
            return sp.logging.info("取消映射操作")

        global SCALE, ROTATION
        SCALE = dialog.result.scale
        ROTATION = dialog.result.rotation

        for texture_set in sp.textureset.all_texture_sets():
            set_name = texture_set.name()
            set_stacks = texture_set.all_stacks()

            if set_name not in dialog.result.texture_sets:
                continue

            try:
                log_info(f"🎨 處理 Texture Set: {set_name}")
                for index, stack in enumerate(set_stacks):
                    for layer in sp.layerstack.get_root_layer_nodes(stack):
                        process_layer_recursive(layer, f"{set_name} / Stack{index}")

            except Exception as e:
                log_info(f"❌ 處理 Texture Set 時發生錯誤: {e}")

        sp.logging.info("映射調整完成")

    except Exception as e:
        sp.logging.info(f"❌ 處理對話框時發生錯誤: {e}")

    finally:
        dialog.deleteLater()
