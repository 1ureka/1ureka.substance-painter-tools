import random
import substance_painter as sp  # type: ignore
from randomize.utils import CollectResult, ProcessResult, Handler


class RandomizeHandler(Handler):
    """
    隨機化處理器，負責處理支援隨機種子的 Substance 來源。

    此處理器會識別和處理包含 $randomseed 參數的 Substance 程序紋理來源，
    為它們生成新的隨機種子值以產生不同的視覺變化。

    支援的圖層類型:
    - FillLayer: 填充圖層
    - FillEffect: 填充效果
    - FilterEffect: 濾鏡效果
    - GeneratorEffect: 生成器效果

    支援 Split Source 模式，可以處理多通道分離的來源，
    也支援嵌套的圖像輸入 (image_inputs)。

    Attributes:
        valid_node_types (tuple): 允許處理的圖層類型元組
    """

    valid_node_types = (
        sp.layerstack.NodeType.FillLayer,
        sp.layerstack.NodeType.FillEffect,
        sp.layerstack.NodeType.FilterEffect,
        sp.layerstack.NodeType.GeneratorEffect,
    )

    @staticmethod
    def validate_source(source: object) -> bool:
        """
        驗證來源是否支援隨機化。

        檢查來源是否為 SourceSubstance 類型，並且其參數中包含 $randomseed 參數。
        只有同時滿足這兩個條件的來源才能被隨機化處理。

        :param source: 來源物件
        :type source: object
        :return: 如果來源支援隨機化返回 True ，否則返回 False
        :rtype: bool
        """
        if not isinstance(source, sp.source.SourceSubstance):
            return False

        try:
            parameters = source.get_parameters()
            return "$randomseed" in parameters
        except Exception as e:
            sp.logging.error(f"驗證來源時發生錯誤: {str(e)}")
            return False

    @staticmethod
    def collect_sources(layer: object) -> CollectResult:
        """
        從圖層中收集所有支援隨機化的來源物件。

        此方法會:
        1. 檢查圖層類型是否在允許的類型中
        2. 根據 source_mode 收集主要來源:
           - Material 模式: 收集材質來源
           - Split 模式: 收集所有活躍通道的來源
           - 其他: 收集單一來源
        3. 驗證每個來源是否支援隨機化
        4. 檢查是否有嵌套的圖像輸入 (image_inputs) 並遞迴收集

        :param layer: Substance Painter 的圖層物件
        :type layer: object
        :return: 收集到的支援隨機化的來源列表
        :rtype: CollectResult
        """
        if layer.get_type() not in RandomizeHandler.valid_node_types:
            return CollectResult(sources=[])

        # 收集主要來源
        sources_from_layer = []
        mode = getattr(layer, "source_mode", None)

        if mode == sp.source.SourceMode.Material:
            sources_from_layer.append(layer.get_material_source())

        elif mode == sp.source.SourceMode.Split:
            for channel in layer.active_channels:
                sources_from_layer.append(layer.get_source(channel))
        else:
            sources_from_layer.append(layer.get_source())

        # 驗證並收集
        sources = []

        for layer_source in sources_from_layer:
            if RandomizeHandler.validate_source(layer_source):
                sources.append(layer_source)

            if not hasattr(layer_source, "image_inputs"):
                continue

            for input_name in layer_source.image_inputs:
                nested_source = layer_source.get_source(input_name)
                if RandomizeHandler.validate_source(nested_source):
                    sources.append(nested_source)

        return CollectResult(sources=sources)

    @staticmethod
    def process_source(source: object, seed: int) -> bool:
        """
        為單一來源設定隨機種子值。

        嘗試將指定的種子值設定到來源的 $randomseed 參數中。
        如果設定成功返回 True ，發生錯誤則記錄錯誤並返回 False。

        :param source: 要設定的來源物件
        :type source: object
        :param seed: 新的隨機種子值
        :type seed: int
        :return: 設定成功返回 True ，失敗返回 False
        :rtype: bool
        """
        try:
            source.set_parameters({"$randomseed": seed})
            return True
        except Exception as e:
            sp.logging.error(f"設置隨機種子時發生錯誤: {str(e)}")
            return False

    @staticmethod
    def process_sources(sources: list[object]) -> ProcessResult:
        """
        批次處理多個來源，為它們設定相同的新隨機種子。

        這個方法會:
        1. 生成一個新的 16 位元隨機種子
        2. 遍歷所有來源，嘗試為每個來源設定這個種子
        3. 統計成功和失敗的數量
        4. 返回處理結果，包含種子值和統計資訊

        所有來源會使用相同的種子值，這樣可以確保整個專案的隨機效果保持一致。

        :param sources: 要處理的來源物件列表
        :type sources: list[object]
        :return: 處理結果，包含新種子、成功數量和失敗數量
        :rtype: ProcessResult
        """

        new_seed = random.getrandbits(16)
        success_count = 0
        failed_count = 0

        for source in sources:
            if RandomizeHandler.process_source(source, new_seed):
                success_count += 1
            else:
                failed_count += 1

        return ProcessResult(
            new_seed=new_seed,
            success_count=success_count,
            failed_count=failed_count,
        )
