import substance_painter as sp  # type: ignore
from transform.utils import LayerHandler, ValidationResult, ProcessResult, ProcessArgs


class FillLayerHandler(LayerHandler):
    allowed_types = {sp.layerstack.NodeType.FillLayer, sp.layerstack.NodeType.FillEffect}
    allowed_mappings = {sp.layerstack.MappingType.UV, sp.layerstack.MappingType.Triplanar}

    @staticmethod
    def _is_split_layer(layer: object) -> bool:
        return hasattr(layer, "source_mode") and layer.source_mode == sp.source.SourceMode.Split

    @staticmethod
    def _validate_source(layer: object, source: object) -> ValidationResult:
        if hasattr(source, "resource_id") and "project" in source.resource_id.context:
            return ValidationResult.reject("填充來源為 Project Resource, 很有可能為烘焙結果而非紋理")

        if hasattr(source, "anchor"):
            return ValidationResult.reject("填充來源為 Anchor")

        if hasattr(source, "get_parameters"):
            procedural_params = ["scale", "tile", "tiling", "pattern_scale"]
            if any(param in source.get_parameters() for param in procedural_params) and "3D" in layer.get_name():
                return ValidationResult.reject("填充來源為 3D Procedural Texture")

        return ValidationResult.ok()

    @staticmethod
    def validate_layer(layer: object) -> ValidationResult:
        layer_type = layer.get_type()

        if layer_type not in FillLayerHandler.allowed_types:
            return ValidationResult.skip(f"圖層類型 {layer_type} 不屬於填充圖層")

        if layer.get_projection_mode() not in FillLayerHandler.allowed_mappings:
            return ValidationResult.reject("填充圖層不是使用 UV 或 Triplanar 映射")

        if layer.source_mode == sp.source.SourceMode.Material:
            if hasattr(layer.get_material_source(), "anchor"):
                return ValidationResult.reject("填充圖層是錨點材質來源")
            return ValidationResult.ok()

        try:
            if FillLayerHandler._is_split_layer(layer):
                sources = [layer.get_source(ch) for ch in layer.active_channels]
                results = [FillLayerHandler._validate_source(layer, src) for src in sources]

                if any(res.status == "rejected" for res in results):
                    reject_reasons = [res.message for res in results if res.status == "rejected"]
                    return ValidationResult.reject("; ".join(reject_reasons))
                elif any(res.status == "skipped" for res in results):
                    skip_reasons = [res.message for res in results if res.status == "skipped"]
                    return ValidationResult.skip("; ".join(skip_reasons))
                else:
                    return ValidationResult.ok()
            else:
                source = layer.get_source()
                return FillLayerHandler._validate_source(layer, source)
        except Exception as e:
            return ValidationResult.reject(f"驗證圖層來源時發生錯誤: {str(e)}")

    @staticmethod
    def process_layer(layer: object, args: ProcessArgs) -> ProcessResult:
        scale_multiplier, rotation_offset = args

        try:
            modif_params = layer.get_projection_parameters()
            changes = []

            if scale_multiplier != 1.0:
                current_scale = modif_params.uv_transformation.scale
                new_scale = [scale * scale_multiplier for scale in current_scale]
                modif_params.uv_transformation.scale = new_scale
                changes.append(f">>> 縮放: <{current_scale} => {new_scale}>")

            if rotation_offset != 0:
                current_rotation = modif_params.uv_transformation.rotation
                new_rotation = (current_rotation + rotation_offset) % 360
                modif_params.uv_transformation.rotation = new_rotation
                changes.append(f">>> 旋轉: <{current_rotation} => {new_rotation}>")

            if not changes:
                return ProcessResult.no_change()

            layer.set_projection_parameters(modif_params)

            return ProcessResult.success("; ".join(changes))
        except Exception as e:
            return ProcessResult.fail(f"處理/應用圖層時發生錯誤: {str(e)}")
