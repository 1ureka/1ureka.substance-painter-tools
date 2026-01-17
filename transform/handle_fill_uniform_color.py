import substance_painter as sp  # type: ignore
from transform.utils import LayerHandler, ValidationResult, ProcessResult, ProcessArgs


class FillUniformColorLayerHandler(LayerHandler):
    """
    純色填充圖層和填充效果的處理器。

    負責攔截 Substance Painter 中所有使用純色 (Uniform Color) 來源的 FillLayer 和 FillEffect 類型圖層。
    純色圖層沒有紋理或映射的概念，因此不需要進行縮放或旋轉調整。

    本處理器會識別以下兩種純色圖層類型:
    - **單通道純色**: 使用單一純色來源 (source_mode 為 Color)
    - **多通道純色**: 使用 Split Source 模式，但所有通道都是純色

    Attributes:
        allowed_types (set): 允許處理的圖層類型集合
    """

    allowed_types = {sp.layerstack.NodeType.FillLayer, sp.layerstack.NodeType.FillEffect}

    @staticmethod
    def _is_split_layer(layer: object) -> bool:
        """
        檢查圖層是否使用 Split Source 模式。

        Split Source 模式允許不同的通道 (如 Base Color、Roughness 等)
        使用不同的填充來源。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :return: 如果是 Split Source 模式返回 True ，否則返回 False
        :rtype: bool
        """
        return hasattr(layer, "source_mode") and layer.source_mode == sp.source.SourceMode.Split

    @staticmethod
    def validate_layer(layer: object) -> ValidationResult:
        """
        驗證圖層是否為純色填充圖層。

        驗證流程:
        1. 檢查圖層類型是否為 FillLayer 或 FillEffect
        2. 跳過 Material 來源模式 (材質不是純色)
        3. 如果是 Split Source ，檢查所有通道是否都是純色
        4. 如果不是 Split Source ，檢查單一來源是否為純色

        只有所有來源都是 SourceUniformColor 的圖層才會被接受處理。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :return: 驗證結果，接受/跳過
        :rtype: ValidationResult
        """
        layer_type = layer.get_type()

        if layer_type not in FillUniformColorLayerHandler.allowed_types:
            return ValidationResult.skip(f"圖層類型 {layer_type} 不屬於填充圖層")

        # 材質來源模式不可能是純色
        if hasattr(layer, "source_mode") and layer.source_mode == sp.source.SourceMode.Material:
            return ValidationResult.skip("圖層是材質來源模式，不是純色")

        try:
            # 檢查 Split Source 模式 (多通道)
            if FillUniformColorLayerHandler._is_split_layer(layer):
                sources = [layer.get_source(ch) for ch in layer.active_channels]

                if not sources:
                    return ValidationResult.skip("Split Source 圖層沒有任何有效來源")

                # 檢查是否所有通道都是純色
                all_uniform_color = all(isinstance(source, sp.source.SourceUniformColor) for source in sources)

                if all_uniform_color:
                    return ValidationResult.ok()
                else:
                    return ValidationResult.skip("Split Source 圖層有部分通道不是純色")
            else:
                # 檢查單一來源
                source = layer.get_source()

                if isinstance(source, sp.source.SourceUniformColor):
                    return ValidationResult.ok()
                else:
                    return ValidationResult.skip("圖層來源不是純色")

        except Exception as e:
            return ValidationResult.skip(f"驗證圖層來源時發生錯誤: {str(e)}")

    @staticmethod
    def process_layer(layer: object, args: ProcessArgs) -> ProcessResult:
        """
        處理純色填充圖層。

        純色圖層沒有紋理或映射，不需要進行任何變換處理。
        此方法只是返回成功狀態並說明圖層類型。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :param args: 處理參數 (未使用)
        :type args: ProcessArgs
        :return: 處理結果，說明圖層是單通道純色還是多通道純色
        :rtype: ProcessResult
        """
        is_split = FillUniformColorLayerHandler._is_split_layer(layer)

        if is_split:
            channel_count = len(layer.active_channels)
            return ProcessResult.success(f"多通道純色圖層 ({channel_count} 個通道)，無需調整")
        else:
            return ProcessResult.success("單通道純色圖層，無需調整")
