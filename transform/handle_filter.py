import substance_painter as sp  # type: ignore
from transform.utils import LayerHandler, ValidationResult, ProcessResult, ProcessArgs
from enum import Enum, auto


class TransformStrategy(Enum):
    INVERSE_SCALE = auto()  # 乘上 1/scale (適用於強度、模糊半徑)
    DIRECT_SCALE = auto()  # 乘上 scale (適用於噪點頻率、縮放)


class FilterLayerHandler(LayerHandler):
    """
    濾鏡效果圖層的處理器。

    負責處理 Substance Painter 中的 FilterEffect 類型的圖層，
    對其濾鏡參數進行物理補償，以確保縮放前後的視覺效果保持一致。

    當圖層或遮罩被縮放時，某些濾鏡參數（如模糊強度、扭曲強度、噪點比例）需要根據縮放比例
    進行對應的調整，才能在物理空間中維持相同的視覺效果。

    Attributes:
        allowed_types (set): 允許處理的圖層類型集合
        allowed_resources (dict): 濾鏡資源 ID 到參數調整策略的映射表，鍵為濾鏡資源 ID (小寫) 值為參數名稱到 TransformStrategy 的字典
    """

    allowed_types = {sp.layerstack.NodeType.FilterEffect}

    # 透過手動用 print 在 Substance Painter 10.0.1 中測試得到的結果
    allowed_resources = {
        "blur/blur": {
            "intensity": TransformStrategy.INVERSE_SCALE,
        },
        "warp/warp": {
            "intensity": TransformStrategy.INVERSE_SCALE,
            "noise_scale": TransformStrategy.DIRECT_SCALE,
        },
        "blur_slope/blur_slope": {
            "intensity": TransformStrategy.INVERSE_SCALE,
            "noise_scale": TransformStrategy.DIRECT_SCALE,
        },
    }

    @staticmethod
    def validate_layer(layer: object) -> ValidationResult:
        """
        驗證圖層是否為可處理的濾鏡效果圖層。

        驗證流程:
        1. 檢查圖層類型是否為 FilterEffect
        2. 檢查圖層是否具有 get_source 方法
        3. 檢查來源是否具有必要的方法和屬性 (get_parameters 和 resource_id)
        4. 檢查濾鏡資源 ID 是否在支援的濾鏡列表中 (allowed_resources)
        5. 檢查來源參數中是否包含該濾鏡所需的所有調整參數

        只有所有檢查都通過的濾鏡效果才會被接受處理。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :return: 驗證結果，接受/跳過/拒絕
        :rtype: ValidationResult
        """
        layer_type = layer.get_type()

        if layer_type not in FilterLayerHandler.allowed_types:
            return ValidationResult.skip(f"圖層類型 {layer_type} 不屬於濾鏡效果圖層")

        if not hasattr(layer, "get_source"):
            return ValidationResult.reject("圖層缺少 get_source 方法")

        source = layer.get_source()

        if not (hasattr(source, "get_parameters") and hasattr(source, "resource_id")):
            return ValidationResult.reject("來源缺少必要方法或屬性")

        res_id = source.resource_id.name.lower()

        if res_id not in FilterLayerHandler.allowed_resources:
            return ValidationResult.reject(f"尚未支援的 Filter 資源: {res_id}")

        params = source.get_parameters()
        required_params = FilterLayerHandler.allowed_resources[res_id].keys()

        missing = [p for p in required_params if p not in params]
        if missing:
            return ValidationResult.reject(f"資源 {res_id} 缺少預期參數: {missing}")

        return ValidationResult.ok()

    @staticmethod
    def process_layer(layer: object, args: ProcessArgs) -> ProcessResult:
        """
        處理濾鏡效果圖層的參數補償。

        處理流程:
        1. 獲取濾鏡來源和資源 ID
        2. 查詢該濾鏡的參數調整策略表
        3. 遍歷每個需要調整的參數
        4. 根據策略計算新參數值
        5. 批次更新所有調整後的參數

        只處理縮放參數，不處理旋轉參數（濾鏡通常沒有旋轉概念）。
        如果沒有任何參數被修改，返回 no_change 結果。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :param args: 處理參數，只使用 scale 值
        :type args: ProcessArgs
        :return: 處理結果，包含成功/無需修改的狀態和詳細訊息
        :rtype: ProcessResult
        """
        source = layer.get_source()
        res_id = source.resource_id.name.lower()
        strategies = FilterLayerHandler.allowed_resources.get(res_id, {})

        current_params = source.get_parameters()
        new_params = {}

        for param_name, strategy in strategies.items():
            old_val = current_params[param_name]

            if strategy == TransformStrategy.INVERSE_SCALE:
                new_params[param_name] = old_val * (1.0 / args.scale)

            elif strategy == TransformStrategy.DIRECT_SCALE:
                new_params[param_name] = old_val * args.scale

            elif strategy == TransformStrategy.ROTATION_OFFSET:
                # 假設 args.rotation 是角度 (0-360)，SP 參數通常是 0-1
                rotation_offset = args.rotation / 360.0
                new_params[param_name] = (old_val + rotation_offset) % 1.0

        if new_params:
            source.set_parameters(new_params)
            return ProcessResult.success(f"已更新 {res_id} 的參數: {list(new_params.keys())}")

        return ProcessResult.no_change()
