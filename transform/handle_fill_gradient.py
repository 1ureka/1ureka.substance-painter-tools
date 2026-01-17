import substance_painter as sp  # type: ignore
from transform.utils import LayerHandler, ValidationResult, ProcessResult, ProcessArgs


class FillGradientLayerHandler(LayerHandler):
    """
    特定漸層填充效果圖層的處理器。

    負責攔截 Substance Painter 中使用特定固定漸層效果的 FillEffect 類型圖層。
    這些漸層通常用於固定的效果（如線性漸層等），不應該隨著圖層縮放而調整，因此需要被攔截並跳過處理。

    注意: 本處理器只處理 FillEffect 圖層，不包括多通道的 FillLayer 圖層。

    Attributes:
        allowed_types (set): 允許處理的圖層類型集合
        allowed_resources (set): 需要攔截的漸層資源 ID 集合 (小寫)
    """

    allowed_types = {sp.layerstack.NodeType.FillEffect}

    # 嚴格定義需要攔截的漸層資源 ID 列表
    allowed_resources = {
        "noise_dirt_gradient/ratio_dirt_gradient",
        "gradient_circular/gradient_circular",
        "gradient_dot/gradient_dot",
        "gradient_linear_3/gradient_linear_3",
        "gradient_linear_2/gradient_linear_2",
        "gradient_linear_1/gradient_linear_1",
    }

    @staticmethod
    def _validate_source(source: object) -> ValidationResult:
        """
        驗證填充來源是否為需要攔截的固定漸層。

        檢查來源的資源 ID 是否在攔截列表中。只有嚴格匹配的漸層才會被攔截。

        :param source: 填充來源物件
        :type source: object
        :return: 驗證結果，接受或跳過
        :rtype: ValidationResult
        """
        if not (hasattr(source, "get_parameters") and hasattr(source, "resource_id")):
            return ValidationResult.skip("來源缺少必要方法或屬性")

        res_id = source.resource_id.name.lower()

        # 嚴格檢查是否在攔截列表中
        if res_id in FillGradientLayerHandler.allowed_resources:
            return ValidationResult.ok()
        else:
            return ValidationResult.skip(f"來源資源 ID {res_id} 不在固定漸層攔截列表中")

    @staticmethod
    def validate_layer(layer: object) -> ValidationResult:
        """
        驗證圖層是否為可處理的漸層填充效果圖層。

        驗證流程:
        1. 檢查圖層類型是否為 FillEffect
        2. 檢查是否為 Material 來源模式
        3. 檢查是否為 Split Source 模式
        4. 驗證來源是否為漸層

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :return: 驗證結果，接受/跳過/拒絕
        :rtype: ValidationResult
        """
        layer_type = layer.get_type()

        if layer_type not in FillGradientLayerHandler.allowed_types:
            return ValidationResult.skip(f"圖層類型 {layer_type} 不屬於漸層填充效果圖層")

        try:
            if hasattr(layer, "source_mode") and layer.source_mode == sp.source.SourceMode.Material:
                return ValidationResult.skip("圖層是材質來源模式，不可能是漸層")

            if hasattr(layer, "source_mode") and layer.source_mode == sp.source.SourceMode.Split:
                return ValidationResult.skip("多通道圖層暫不支援漸層處理")
            else:
                source = layer.get_source()
                return FillGradientLayerHandler._validate_source(source)

        except Exception as e:
            return ValidationResult.reject(f"驗證圖層來源時發生錯誤: {str(e)}")

    @staticmethod
    def process_layer(layer: object, args: ProcessArgs) -> ProcessResult:
        """
        處理固定漸層填充效果圖層。

        固定漸層效果（如線性漸層與變體、圓形漸層等）不應隨著圖層縮放而調整，
        因此本方法只返回成功狀態，不進行任何實際處理。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :param args: 處理參數（未使用）
        :type args: ProcessArgs
        :return: 處理結果，說明此漸層被跳過處理
        :rtype: ProcessResult
        """
        source = layer.get_source()

        return ProcessResult.success(f"固定漸層 {source.resource_id.name} 通常與幾何直接相關，被跳過處理")
