import substance_painter as sp  # type: ignore
from transform.utils import LayerHandler, ValidationResult, ProcessResult, ProcessArgs


class Fill3DLayerHandler(LayerHandler):
    """
    3D 程序紋理填充圖層的處理器。

    負責處理 Substance Painter 中使用 3D Procedural Texture (如 3D Perlin Noise、3D Worley Noise 等)
    的 FillLayer 和 FillEffect 類型的圖層，對其縮放相關參數進行調整。

    3D 程序紋理使用體積採樣而非 UV 映射，因此其縮放參數名稱與普通填充圖層不同。
    本處理器會自動識別 3D 紋理類型，並調整對應的縮放參數。

    支援 Split Source 模式，可以處理多通道分離的 3D 紋理來源。

    Attributes:
        allowed_types (set): 允許處理的圖層類型集合
        procedural_params (list): 3D 程序紋理的縮放參數關鍵字列表，按優先級排序。
                                 處理時只會調整第一個匹配到的參數。
        procedural_keywords (dict): 用於識別 3D 程序紋理的關鍵字集合，鍵為紋理名稱，
                                   值為該紋理名稱中必須包含的關鍵字集合
    """

    allowed_types = {sp.layerstack.NodeType.FillLayer, sp.layerstack.NodeType.FillEffect}

    procedural_params = [
        "scale",
        "tile",
        "tiling",
        "pattern_scale",
    ]

    procedural_keywords = {
        "3D Perlin Noise": {"3d", "perlin", "noise"},
        "3D Worley Noise": {"3d", "worley", "noise"},
        "3D Voronoi": {"3d", "voronoi"},
        "3D Ridged Noise": {"3d", "ridged", "noise"},
        "3D Simplex Noise": {"3d", "simplex", "noise"},
    }

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
    def _validate_source(source: object) -> ValidationResult:
        """
        驗證填充來源是否為 3D 程序紋理。

        檢查來源是否同時滿足以下條件:
        1. 具有必要的方法和屬性 (get_parameters 和 resource_id)
        2. 參數中包含 procedural_params 列表中的至少一個參數
        3. 來源名稱中包含 procedural_keywords 中定義的某組關鍵字

        只有同時滿足參數匹配和關鍵字匹配的來源才會被接受處理。

        :param source: 填充來源物件
        :type source: object
        :return: 驗證結果，接受或跳過
        :rtype: ValidationResult
        """

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
        """
        驗證圖層是否為可處理的 3D 程序紋理填充圖層。

        驗證流程:
        1. 檢查圖層類型是否為 FillLayer 或 FillEffect
        2. 檢查是否為 Material 來源模式 (3D 紋理不會使用材質模式)
        3. 如果是 Split Source ，驗證每個通道的來源是否為 3D 紋理
        4. 如果不是 Split Source ，驗證單一來源是否為 3D 紋理

        對於 Split Source 圖層，只要有任何一個通道被拒絕就返回拒絕結果；
        如果所有通道都被跳過則返回跳過結果；只有所有通道都接受才返回接受結果。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :return: 驗證結果，接受/跳過/拒絕
        :rtype: ValidationResult
        """

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
        """
        處理 3D 程序紋理填充圖層的縮放參數。
        根據 `Fill3DLayerHandler.procedural_params` 列表的順序，搜尋並只調整第一個匹配的縮放參數，避免重複縮放。

        處理流程:
        1. 獲取所有來源成 list (單一或多通道)
        2. 對每個來源找到要修改的縮放參數，並記錄到目標清單中
        3. 根據縮放倍數調整參數值:
          - 整數參數: 乘以縮放倍數並四捨五入，最小值為 1
          - 浮點數參數: 乘以縮放倍數，最小值為 0.1
        4. 根據目標清單再次獲取來源的實際值，並對比修改前的紀錄是否有任何變化

        只處理縮放參數，不處理旋轉參數 (3D 紋理通常沒有旋轉參數) 。
        如果縮放倍數為 1.0 或沒有找到任何可調整的參數，返回 no_change 結果。

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :param args: 處理參數，只使用 scale 值
        :type args: ProcessArgs
        :return: 處理結果，包含成功/失敗/無需修改的狀態和詳細訊息
        :rtype: ProcessResult
        """

        scale_multiplier = args.scale

        if scale_multiplier == 1.0:
            return ProcessResult.no_change()

        def process_sources(sources: list[tuple]) -> ProcessResult:
            """處理所有來源的縮放參數，批次應用修改後驗證實際變化。"""

            # 遍歷所有來源，找到每個來源的第一個匹配參數並記錄
            targets: list[tuple[object, object, str, any]] = []  # 記錄格式: (channel, source, target_key, old_value)

            for channel, source in sources:
                if not hasattr(source, "get_parameters"):
                    continue

                params: dict[str, any] = source.get_parameters()
                target_key = None
                old_value = None

                # 按優先級順序查找第一個匹配的參數鍵
                for param_key in Fill3DLayerHandler.procedural_params:
                    for key, value in params.items():
                        if param_key in key.lower() and type(value) in (int, float):
                            target_key = key
                            old_value = value
                            break
                    if target_key:
                        break

                if target_key:
                    targets.append((channel, source, target_key, old_value))

            if not targets:
                return ProcessResult.no_change()

            # 批次應用所有修改
            for channel, source, target_key, old_value in targets:
                params = source.get_parameters()

                if type(old_value) is int:
                    new_value = int(max(1, round(old_value * scale_multiplier)))
                elif type(old_value) is float:
                    new_value = float(max(0.1, old_value * scale_multiplier))
                else:
                    continue

                params[target_key] = new_value
                source.set_parameters(params)

            # 重新獲取所有來源的實際值，對比是否有變化
            changes: list[str] = []

            for channel, source, target_key, old_value in targets:
                actual_params = source.get_parameters()
                actual_value = actual_params.get(target_key)

                if actual_value != old_value:
                    channel_info = f"通道 {channel} 的" if channel else ""
                    changes.append(f"{channel_info}參數 {target_key}: {old_value} => {actual_value}")

            # 根據變化情況返回結果
            if not changes:
                return ProcessResult.no_change()

            return ProcessResult.success("; ".join(changes))

        try:
            sources = []
            if Fill3DLayerHandler._is_split_layer(layer):
                sources = [(ch, layer.get_source(ch)) for ch in layer.active_channels]
            else:
                sources = [(None, layer.get_source())]

            return process_sources(sources)

        except Exception as e:
            return ProcessResult.fail(f"處理 3D 紋理圖層時發生錯誤: {str(e)}")
