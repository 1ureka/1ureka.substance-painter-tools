import substance_painter as sp  # type: ignore
from transform.utils import LayerHandler, ValidationResult, ProcessResult, ProcessArgs


class FillLayerHandler(LayerHandler):
    """
    填充圖層和填充效果的處理器。

    負責處理 Substance Painter 中的 FillLayer 和 FillEffect 類型的圖層，
    對其 UV 變換參數（縮放和旋轉）進行調整。

    只處理使用 UV 或 Triplanar 映射的圖層，並會自動排除:
    - Anchor 錦點圖層
    - Project Resource （通常是烘焙結果）
    - 3D Procedural Texture

    支援 Split Source 模式，可以處理多通道分離的填充來源。

    Attributes:
        allowed_types (set): 允許處理的圖層類型集合
        allowed_mappings (set): 允許處理的映射類型集合
        procedural_params (list): 3D 紋理的參數關鍵字列表
    """

    allowed_types = {sp.layerstack.NodeType.FillLayer, sp.layerstack.NodeType.FillEffect}
    allowed_mappings = {sp.layerstack.ProjectionMode.UV, sp.layerstack.ProjectionMode.Triplanar}
    procedural_params = ["scale", "tile", "tiling", "pattern_scale"]

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
        """
        驗證填充來源是否符合處理條件。

        檢查來源是否為以下不應處理的類型:
        - Project Resource: 通常是烘焙結果，不應修改
        - Anchor: 錦點圖層，不應修改
        - 3D Procedural Texture: 特殊的 3D 程序紋理，不應修改

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :param source: 填充來源物件
        :type source: object
        :return: 驗證結果，接受或拒絕
        :rtype: ValidationResult
        """
        if hasattr(source, "resource_id") and "project" in source.resource_id.context:
            return ValidationResult.reject("填充來源為 Project Resource, 很有可能為烘焙結果而非紋理")

        if hasattr(source, "anchor"):
            return ValidationResult.reject("填充來源為 Anchor")

        if hasattr(source, "get_parameters") and hasattr(source, "resource_id"):
            is_3d_texture = "3d" in source.resource_id.name.lower()
            param_matches = [param in source.get_parameters() for param in FillLayerHandler.procedural_params]

            if is_3d_texture and any(param_matches):
                return ValidationResult.reject("填充來源為 3D 生成紋理")

        return ValidationResult.ok()

    @staticmethod
    def validate_layer(layer: object) -> ValidationResult:
        """
        驗證圖層是否為可處理的填充圖層或填充效果。

        驗證流程:
        1. 檢查圖層類型是否為 FillLayer 或 FillEffect
        2. 檢查映射模式是否為 UV 或 Triplanar
        3. 如果是 Material 來源模式，檢查是否為錦點
        4. 如果是 Split Source ，驗證每個通道的來源
        5. 如果不是 Split Source ，驗證單一來源

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :return: 驗證結果，接受/跳過/拒絕
        :rtype: ValidationResult
        """
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

                if not sources:
                    return ValidationResult.reject("圖層沒有任何通道")

                results = [FillLayerHandler._validate_source(source) for source in sources]

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
                return FillLayerHandler._validate_source(source)
        except Exception as e:
            return ValidationResult.reject(f"驗證圖層來源時發生錯誤: {str(e)}")

    @staticmethod
    def process_layer(layer: object, args: ProcessArgs) -> ProcessResult:
        """
        處理填充圖層的 UV 變換參數。

        根據提供的參數調整圖層的:
        - 縮放 (scale): 將當前縮放值乘以縮放倍數
        - 旋轉 (rotation): 將當前旋轉角度加上旋轉偏移量

        如果縮放倍數為 1.0 且旋轉偏移量為 0 ，則返回 no_change 結果。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :param args: 處理參數，包含縮放倍數和旋轉偏移量
        :type args: ProcessArgs
        :return: 處理結果，包含成功/失敗/無需修改的狀態和詳細訊息
        :rtype: ProcessResult
        """
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
