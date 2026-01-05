import random
import substance_painter as sp  # type: ignore
from randomize.utils import CollectResult, ProcessResult, Handler


class RandomizeHandler(Handler):
    """?"""

    valid_node_types = (
        sp.layerstack.NodeType.FillLayer,
        sp.layerstack.NodeType.FillEffect,
        sp.layerstack.NodeType.FilterEffect,
        sp.layerstack.NodeType.GeneratorEffect,
    )

    @staticmethod
    def validate_source(source: object) -> bool:
        """?"""
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
        """?"""
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
        """?"""
        try:
            source.set_parameters({"$randomseed": seed})
            return True
        except Exception as e:
            sp.logging.error(f"設置隨機種子時發生錯誤: {str(e)}")
            return False

    @staticmethod
    def process_sources(sources: list[object]) -> ProcessResult:
        """?"""

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
