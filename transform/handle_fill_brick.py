import substance_painter as sp  # type: ignore
from transform.utils import LayerHandler, ValidationResult, ProcessResult, ProcessArgs


class FillBrickLayerHandler(LayerHandler):
    """
    磚塊生成器填充效果圖層的處理器。

    負責處理 Substance Painter 中使用磚塊生成器 (Brick Generator) 的 FillEffect 類型圖層，
    調整磚塊數量 (Bricks) 參數以確保縮放前後的視覺效果保持一致。

    當圖層被縮放時，只需要調整磚塊數量。例如，紋理放大 2 倍後，磚塊數量需要加倍
    才能維持相同的磚塊大小。其他參數 (如 Bevel、Gap、Middle_Size 等) 都是相對於
    磚塊大小的比例，會自動隨著磚塊數量調整而保持正確的視覺效果，不需要額外處理。

    支援的磚塊生成器:
    - **Ratio Brick Generator**: 調整磚塊數量 (Bricks) 參數

    注意: 本處理器只處理 FillEffect 圖層，不包括多通道的 FillLayer 圖層，
    因為多通道圖層的處理邏輯較為複雜且磚塊生成器通常作為效果使用。

    Attributes:
        allowed_types (set): 允許處理的圖層類型集合
        allowed_resources (set): 支援的磚塊生成器資源 ID 集合 (小寫)
    """

    allowed_types = {sp.layerstack.NodeType.FillEffect}

    # 透過手動用 print 在 Substance Painter 10.0.1 中測試得到的結果
    # [Python] brick_generator/ratio_brick_generator
    # [Python] {'tile_by_ratio': 0, 'invert': 0, 'histogram_position': 0.5, 'historgram_contrast': 0.0, 'Bricks': (4, 4), 'Bevel': (0.5, 0.5, 0.0, 0.0), 'Keep_Ratio': 0, 'Gap': (0.0, 0.0), 'Middle_Size': (0.5, 0.5), 'Height': (1.0, 1.0, 0.0, 0.0), 'Slope': (0.0, 0.0, 0.0, 0.0), 'Offset': (0.5, 0.0)}
    allowed_resources = {"brick_generator/ratio_brick_generator"}

    @staticmethod
    def _validate_source(source: object) -> ValidationResult:
        """
        驗證填充來源是否為磚塊生成器。

        檢查來源是否同時滿足以下條件:
        1. 具有必要的方法和屬性 (get_parameters 和 resource_id)
        2. 資源 ID 在支援的磚塊生成器列表中
        3. 參數中包含 Bricks 參數

        只有同時滿足所有條件的來源才會被接受處理。

        :param source: 填充來源物件
        :type source: object
        :return: 驗證結果，接受或跳過
        :rtype: ValidationResult
        """
        if not (hasattr(source, "get_parameters") and hasattr(source, "resource_id")):
            return ValidationResult.skip("來源缺少必要方法或屬性")

        res_id = source.resource_id.name.lower()

        if res_id not in FillBrickLayerHandler.allowed_resources:
            return ValidationResult.skip(f"來源資源 ID {res_id} 不在支援列表中")

        params = source.get_parameters()
        if "Bricks" not in params:
            return ValidationResult.skip("磚塊生成器缺少 Bricks 參數")

        return ValidationResult.ok()

    @staticmethod
    def validate_layer(layer: object) -> ValidationResult:
        """
        驗證圖層是否為可處理的磚塊生成器填充效果圖層。

        驗證流程:
        1. 檢查圖層類型是否為 FillEffect
        2. 檢查是否為 Material 來源模式 (磚塊生成器不會使用材質模式)
        3. 檢查是否為 Split Source 模式 (多通道圖層不支援)
        4. 驗證來源是否為支援的磚塊生成器

        只有所有檢查都通過的磚塊生成器圖層才會被接受處理。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :return: 驗證結果，接受/跳過/拒絕
        :rtype: ValidationResult
        """
        layer_type = layer.get_type()

        if layer_type not in FillBrickLayerHandler.allowed_types:
            return ValidationResult.skip(f"圖層類型 {layer_type} 不屬於磚塊生成器填充效果圖層")

        try:
            if layer.source_mode == sp.source.SourceMode.Material:
                return ValidationResult.skip("圖層是材質來源模式，不可能是磚塊生成器")

            if hasattr(layer, "source_mode") and layer.source_mode == sp.source.SourceMode.Split:
                return ValidationResult.skip("多通道圖層不支援磚塊生成器處理")
            else:
                source = layer.get_source()
                return FillBrickLayerHandler._validate_source(source)

        except Exception as e:
            return ValidationResult.reject(f"驗證圖層來源時發生錯誤: {str(e)}")

    @staticmethod
    def process_layer(layer: object, args: ProcessArgs) -> ProcessResult:
        """
        處理磚塊生成器填充效果圖層的參數補償。

        根據縮放比例調整磚塊數量，以維持相同的磚塊大小。
        Bricks 參數是 (int, int) tuple ，分別代表水平和垂直方向的磚塊數量。
        縮放倍數會同時應用到兩個方向。

        只處理縮放參數，不處理旋轉參數 (磚塊生成器沒有旋轉概念)。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :param args: 處理參數，只使用 scale 值
        :type args: ProcessArgs
        :return: 處理結果，包含成功狀態和詳細訊息
        :rtype: ProcessResult
        """
        source = layer.get_source()
        current_params = source.get_parameters()

        old_bricks = current_params["Bricks"]
        new_bricks = tuple(int(max(1, round(v * args.scale))) for v in old_bricks)

        source.set_parameters({"Bricks": new_bricks})
        return ProcessResult.success(f"磚塊數量從 {old_bricks} 調整為 {new_bricks}")
