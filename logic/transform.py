import substance_painter as sp  # type: ignore
from PySide2 import QtWidgets  # type: ignore

from typing import Callable, Union, Optional, TypedDict, Literal
import importlib
import ui.texture_sets_select as texture_sets_select
import ui.transform_result_dialog as transform_result_dialog

importlib.reload(texture_sets_select)
importlib.reload(transform_result_dialog)

# -------------------------------------------------------------------------
# 工具函數
# -------------------------------------------------------------------------


class TransformContext:
    scale: float = 1.0
    rotation: float = 0.0

    class PathChange(TypedDict):
        type: Literal["skip", "error", "success"]
        layer_type: str
        messages: list[str]  # reasons, changes etc.

    changesByPath: dict[str, PathChange] = {}

    @classmethod
    def add_success(this, path: str, layer_type: str, messages: list[str]) -> None:
        this.changesByPath[path] = {"type": "success", "layer_type": layer_type, "messages": messages}

    @classmethod
    def add_skip(this, path: str, layer_type: str, messages: list[str]) -> None:
        this.changesByPath[path] = {"type": "skip", "layer_type": layer_type, "messages": messages}

    @classmethod
    def add_error(this, path: str, layer_type: str, messages: list[str]) -> None:
        this.changesByPath[path] = {"type": "error", "layer_type": layer_type, "messages": messages}

    @classmethod
    def reset_changes(this) -> None:
        this.changesByPath.clear()

    @classmethod
    def get_result(this) -> dict[str, PathChange]:
        return this.changesByPath


def validate_and_apply(
    layer: object,
    full_path: str,
    layer_type: str,
    is_valid: Union[Callable[[object], tuple[bool, str]], Callable[[object, str], tuple[bool, str]]],
    apply: Callable[[object], list[str]],
    channels: Optional[list[str]] = None,
) -> None:
    if channels:
        results = [is_valid(layer, ch) for ch in channels]
        if all(ok for ok, _ in results):
            TransformContext.add_success(full_path, layer_type, messages=apply(layer))
        else:
            reasons = ", ".join(reason for ok, reason in results if not ok)
            TransformContext.add_skip(full_path, layer_type, messages=[reasons])

    else:
        ok, reason = is_valid(layer)
        if ok:
            TransformContext.add_success(full_path, layer_type, messages=apply(layer))
        else:
            TransformContext.add_skip(full_path, layer_type, messages=[reason])


def create_handle_fill():
    def is_split_layer(layer) -> bool:
        return hasattr(layer, "source_mode") and layer.source_mode == sp.source.SourceMode.Split

    def is_valid_material(layer) -> tuple[bool, str]:
        if hasattr(layer.get_material_source(), "anchor"):
            return (False, "來源為 Anchor")

        return (True, "")

    def is_valid(layer, channel_name: Optional[str] = None) -> tuple[bool, str]:
        modes = [sp.layerstack.ProjectionMode.UV, sp.layerstack.ProjectionMode.Triplanar]
        if layer.get_projection_mode() not in modes:
            return (False, "不是使用 UV 或 Triplanar 映射")

        if layer.source_mode == sp.source.SourceMode.Material:
            return is_valid_material(layer)

        try:
            source = layer.get_source(channel_name) if channel_name else layer.get_source()
        except Exception:
            return (False, "來源為 None")

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

    def apply(layer) -> list[str]:
        modif_params = layer.get_projection_parameters()
        changes = []

        if TransformContext.scale != 1.0:
            current_scale = modif_params.uv_transformation.scale
            new_scale = [scale * TransformContext.scale for scale in current_scale]
            modif_params.uv_transformation.scale = new_scale
            changes.append(f">>> 縮放: <{current_scale} => {new_scale}>")

        if TransformContext.rotation != 0:
            current_rotation = modif_params.uv_transformation.rotation
            new_rotation = (current_rotation + TransformContext.rotation) % 360
            modif_params.uv_transformation.rotation = new_rotation
            changes.append(f">>> 旋轉: <{current_rotation} => {new_rotation}>")

        if not changes:
            return ["⚠️ 找不到可變換的參數"]

        layer.set_projection_parameters(modif_params)
        return changes

    def main(layer, full_path: str) -> None:
        if is_split_layer(layer):
            validate_and_apply(layer, full_path, "Split Layer", is_valid, apply, layer.active_channels)
        else:
            validate_and_apply(layer, full_path, "Single Layer", is_valid, apply)

    return main


def create_handle_generator():
    def is_valid(layer) -> tuple[bool, str]:
        source = layer.get_source()
        if not source:
            return (False, "來源為 None")

        keys = [key.lower() for key in source.get_parameters().keys()]
        rules = {
            "Mask Editor": ["scale", "ao", "curvature", "position"],
            "Mask Builder": ["scale", "ao", "curvature", "grunge"],  # 也包含新版 Dirt, Metal Edge Wear 等
            "Metal Edge Wear": ["scale", "curvature", "wear"],  # 對舊版 Metal Edge Wear 的兼容
        }

        suspect: Optional[tuple[str, int]] = None
        for name, keywords in rules.items():
            missing = [kw for kw in keywords if not any(kw in key for key in keys)]

            if not missing:
                return (True, "")

            elif len(missing) < len(keywords):
                if suspect is None or len(missing) < suspect[1]:
                    suspect = (f"{name} based 生成器疑似，但缺少參數: {', '.join(missing)}", len(missing))

        if suspect:
            return (False, suspect[0])

        return (False, "未知的 Generator 類型")

    def apply(layer) -> list[str]:
        modif_params = layer.get_source().get_parameters()
        updated_params: dict[str, tuple[float, float]] = {}

        for k, v in modif_params.items():
            if not (isinstance(k, str) and "scale" in k.lower()):
                continue

            new_value = v
            if type(v) is int:
                new_value = int(max(1, round(v * TransformContext.scale)))
            elif type(v) is float:
                new_value = float(max(0.1, v * TransformContext.scale))

            if new_value != v:
                updated_params[k] = (v, new_value)
                modif_params[k] = new_value

        if updated_params:
            changes = [f"生成器參數 <{k}> 變換: <{old} => {new}>" for k, (old, new) in updated_params.items()]
            layer.get_source().set_parameters(modif_params)
            return changes
        else:
            return ["⚠️ 找不到可變換的 scale 參數"]

    def main(layer, full_path: str) -> None:
        validate_and_apply(layer, full_path, "Generator", is_valid, apply)

    return main


def create_handle_filter():
    def is_valid(layer) -> tuple[bool, str]:
        # TODO: 過濾出名稱帶有 MatFinish 的 MatFinish 系列濾鏡
        return (False, "非 MatFinish 系列濾鏡")

    def apply(layer) -> list[str]:
        # TODO: 將 MatFinish 系列濾鏡中的參數 "scale" 調整
        return []

    def main(layer, full_path: str) -> None:
        validate_and_apply(layer, full_path, "Filter", is_valid, apply)

    return main


def create_handle_group():
    def main(layer, full_path: str) -> None:
        if not layer.is_visible():
            TransformContext.add_skip(full_path, layer.get_type().__str__(), ["不可見的 Group Layer"])
            return

        for sub_layer in list(layer.sub_layers()):
            process_layer(sub_layer, full_path)

    return main


# -------------------------------------------------------------------------
# 主要函數
# -------------------------------------------------------------------------

Handlers = {
    sp.layerstack.NodeType.GroupLayer: create_handle_group(),
    sp.layerstack.NodeType.GeneratorEffect: create_handle_generator(),
    sp.layerstack.NodeType.FillLayer: create_handle_fill(),
    sp.layerstack.NodeType.FillEffect: create_handle_fill(),
    sp.layerstack.NodeType.FilterEffect: create_handle_filter(),
}


def process_layer(layer, layer_path: str = ""):
    layer_name = layer.get_name()
    layer_type = layer.get_type()
    full_path = f"{layer_path} / {layer_name}" if layer_path else layer_name

    handler = Handlers.get(layer_type)
    if handler:
        try:
            handler(layer, full_path)
        except Exception as e:
            TransformContext.add_error(full_path, str(layer_type), messages=[f"處理 {full_path} 時發生錯誤: {e}"])
    else:
        TransformContext.add_skip(full_path, str(layer_type), messages=["非可處理圖層"])

    if hasattr(layer, "content_effects") and layer.content_effects():
        for effect in layer.content_effects():
            process_layer(effect, f"{full_path} / ContentEffects")

    if hasattr(layer, "mask_effects") and layer.mask_effects():
        for effect in layer.mask_effects():
            process_layer(effect, f"{full_path} / MaskEffects")


# -------------------------------------------------------------------------
# 主流程
# -------------------------------------------------------------------------


def main():
    # ------ 準備對話框所需資料 ------
    if not sp.project.is_open():
        return sp.logging.warning("未開啟任何專案，請先開啟一個專案。")

    active_set = sp.textureset.get_active_stack().name() or str(sp.textureset.get_active_stack())
    rows = [
        texture_sets_select.Row(texture_set.name(), texture_set.name() == active_set)
        for texture_set in sp.textureset.all_texture_sets()
    ]

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
            dialog.destroyed.connect(lambda: sp.logging.info("已正確釋放紋理集選取對話框資源"))
            dialog.deleteLater()

    # ------ 邏輯處理 ------
    TransformContext.scale = result.scale
    TransformContext.rotation = result.rotation
    TransformContext.reset_changes()

    with sp.layerstack.ScopedModification("映射變換"):
        for texture_set in sp.textureset.all_texture_sets():
            set_name = texture_set.name()
            set_stacks = texture_set.all_stacks()

            if set_name not in result.texture_sets:
                continue

            try:
                for index, stack in enumerate(set_stacks):
                    for layer in sp.layerstack.get_root_layer_nodes(stack):
                        process_layer(layer, f"{set_name} / Stack{index}")

            except Exception as e:
                sp.logging.error(f"❌ 處理 Texture Set 時發生錯誤: {e}")

    # ------ 顯示結果對話框 ------
    result_dialog: Optional[transform_result_dialog.Dialog] = None

    try:
        result_data = TransformContext.get_result()
        result_dialog = transform_result_dialog.Dialog(result_data, sp.ui.get_main_window())
        result_dialog.exec_()

    except Exception as e:
        sp.logging.error(f"❌ 顯示結果對話框時發生錯誤: {e}")

    finally:
        if result_dialog:
            result_dialog.destroyed.connect(lambda: sp.logging.info("已正確釋放映射變換結果對話框資源"))
            result_dialog.deleteLater()
