import substance_painter as sp  # type: ignore
from transform.utils import LayerHandler, ValidationResult, ProcessResult, ProcessArgs


class Fill3DLayerHandler(LayerHandler):
    allowed_types = {sp.layerstack.NodeType.FillLayer, sp.layerstack.NodeType.FillEffect}

    procedural_params = [
        "scale",
        "tile",
        "tiling",
        "pattern_scale",
    ]  # TODO: 將該解釋寫成 docstring 3D Procedural Texture 參數關鍵字的同時也是優先級順序 (只會應用第一個匹配的)

    # 在 resource_id.name 中尋找這些關鍵字來判斷是否為要處理的 3D 生成紋理
    procedural_keywords = {"3D Perlin Noise": {"3d", "perlin", "noise"}}

    @staticmethod
    def _is_split_layer(layer: object) -> bool:
        """
        檢查圖層是否使用 Split Source 模式。

        Split Source 模式允許不同的通道（如 Base Color、Roughness 等）
        使用不同的填充來源。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :return: 如果是 Split Source 模式返回 True ，否則返回 False
        :rtype: bool
        """
        return hasattr(layer, "source_mode") and layer.source_mode == sp.source.SourceMode.Split

    @staticmethod
    def _validate_source(source: object) -> ValidationResult:
        if not (hasattr(source, "get_parameters") or hasattr(source, "resource_id")):
            return ValidationResult.skip("來源缺少必要方法或屬性")

        source_params = source.get_parameters()
        has_matching_param = any(param in source_params for param in Fill3DLayerHandler.procedural_params)

        source_name: str = source.resource_id.name.lower()
        has_matching_keyword = any(
            all(keyword in source_name for keyword in keywords)
            for keywords in Fill3DLayerHandler.procedural_keywords.values()
        )

        if has_matching_param and has_matching_keyword:
            return ValidationResult.ok()
        else:
            return ValidationResult.skip("圖層來源不符合 3D 紋理的處理條件")

    @staticmethod
    def validate_layer(layer: object) -> ValidationResult:
        layer_type = layer.get_type()

        if layer_type not in Fill3DLayerHandler.allowed_types:
            return ValidationResult.skip(f"圖層類型 {layer_type} 不屬於使用 3D 紋理的填充圖層")

        if layer.source_mode == sp.source.SourceMode.Material:
            return ValidationResult.skip("圖層是材質來源模式，不可能是 3D 紋理")

        try:
            if Fill3DLayerHandler._is_split_layer(layer):
                sources = [layer.get_source(ch) for ch in layer.active_channels]

                if not sources:
                    return ValidationResult.skip("Split Source 圖層沒有任何有效來源")

                results = [Fill3DLayerHandler._validate_source(source) for source in sources]

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
                return Fill3DLayerHandler._validate_source(source)

        except Exception as e:
            return ValidationResult.reject(f"驗證圖層來源時發生錯誤: {str(e)}")

    @staticmethod
    def process_layer(layer: object, args: ProcessArgs) -> ProcessResult:
        scale_multiplier, rotation_offset = args

        # TODO: 實作 3D 紋理的縮放處理邏輯

        return ProcessResult.no_change()
