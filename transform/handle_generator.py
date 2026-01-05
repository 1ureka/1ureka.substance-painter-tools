import substance_painter as sp  # type: ignore
from typing import Optional
from transform.utils import LayerHandler, ValidationResult, ProcessResult, ProcessArgs


class GeneratorLayerHandler(LayerHandler):
    """
    生成器效果圖層的處理器。

    負責處理 Substance Painter 中的 GeneratorEffect 類型的圖層，
    對其生成器參數中的 scale 相關參數進行調整。

    根據參數特徵自動識別生成器類型，并驗證是否具備必要的參數。

    Attributes:
        allowed_types (set): 允許處理的圖層類型集合
        source_param_rules (dict): 生成器類型到必要參數的映射規則
    """

    allowed_types = {sp.layerstack.NodeType.GeneratorEffect}
    source_param_rules = {
        "Mask Editor": ["scale", "ao", "curvature", "position"],
        "Mask Builder": ["scale", "ao", "curvature", "grunge"],  # 也包含新版 Dirt, Metal Edge Wear 等
        "Metal Edge Wear": ["scale", "curvature", "wear"],  # 對舊版 Metal Edge Wear 的兼容
    }

    @staticmethod
    def validate_layer(layer: object) -> ValidationResult:
        """
        驗證圖層是否為可處理的生成器效果圖層。

        驗證流程:
        1. 檢查圖層類型是否為 GeneratorEffect
        2. 檢查圖層是否有來源
        3. 獲取來源的所有參數鍵
        4. 根據 source_param_rules 檢查是否匹配已知的生成器類型
        5. 如果完全匹配某個規則，返回 accepted
        6. 如果部分匹配，記錄缺少的參數，最後返回 rejected 並說明
        7. 如果完全不匹配，返回 rejected

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :return: 驗證結果，接受/跳過/拒絕
        :rtype: ValidationResult
        """
        layer_type = layer.get_type()

        if layer_type not in GeneratorLayerHandler.allowed_types:
            return ValidationResult.skip(f"圖層類型 {layer_type} 不屬於產生器圖層")

        source = layer.get_source()
        if not source:
            return ValidationResult.reject("產生器圖層沒有來源")

        keys = [key.lower() for key in source.get_parameters().keys()]
        suspect: Optional[tuple[str, int]] = None

        for name, keywords in GeneratorLayerHandler.source_param_rules.items():
            missing = [kw for kw in keywords if not any(kw in key for key in keys)]

            if not missing:
                return ValidationResult.ok()
            elif len(missing) < len(keywords):
                if suspect is None or len(missing) < suspect[1]:
                    suspect = (f"{name} based 生成器疑似，但缺少參數: {', '.join(missing)}", len(missing))

        if suspect:
            return ValidationResult.reject(suspect[0])

        return ValidationResult.reject("產生器圖層來源不符合已知規則")

    @staticmethod
    def process_layer(layer: object, args: ProcessArgs) -> ProcessResult:
        """
        處理生成器效果圖層的 scale 相關參數。

        搜尋生成器參數中所有包含 "scale" 字樣的參數，並根據縮放倍數調整:
        - 整數參數: 乘以縮放倍數並四捨五入，最小值為 1
        - 浮點數參數: 乘以縮放倍數，最小值為 0.1

        只處理縮放參數，不處理旋轉參數 (生成器通常沒有旋轉參數) 。
        如果沒有任何 scale 參數被修改，返回 no_change 結果。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :param args: 處理參數，只使用 scale 值
        :type args: ProcessArgs
        :return: 處理結果，包含成功/無需修改的狀態和詳細訊息
        :rtype: ProcessResult
        """
        scale_multiplier = args.scale

        modif_params = layer.get_source().get_parameters()
        updated_params: dict[str, tuple[float, float]] = {}

        for k, v in modif_params.items():
            if not (isinstance(k, str) and "scale" in k.lower()):
                continue

            new_value = v
            if type(v) is int:
                new_value = int(max(1, round(v * scale_multiplier)))
            elif type(v) is float:
                new_value = float(max(0.1, v * scale_multiplier))

            if new_value != v:
                updated_params[k] = (v, new_value)
                modif_params[k] = new_value

        if updated_params:
            changes = [f"生成器參數 <{k}> 變換: <{old} => {new}>" for k, (old, new) in updated_params.items()]
            layer.get_source().set_parameters(modif_params)
            return ProcessResult.success("; ".join(changes))
        else:
            return ProcessResult.no_change()
