import substance_painter as sp  # type: ignore
from typing import Optional
from transform.utils import LayerHandler, ValidationResult, ProcessResult, ProcessArgs

class GeneratorLayerHandler(LayerHandler):
    allowed_types = {sp.layerstack.NodeType.GeneratorEffect}
    source_param_rules = {
        "Mask Editor": ["scale", "ao", "curvature", "position"],
        "Mask Builder": ["scale", "ao", "curvature", "grunge"],  # 也包含新版 Dirt, Metal Edge Wear 等
        "Metal Edge Wear": ["scale", "curvature", "wear"],  # 對舊版 Metal Edge Wear 的兼容
    }

    @staticmethod
    def validate_layer(layer: object) -> ValidationResult:
        layer_type = layer.get_type()

        if layer_type not in GeneratorLayerHandler.allowed_types:
            return ValidationResult.skip(f'圖層類型 {layer_type} 不屬於產生器圖層')

        source = layer.get_source()
        if not source:
            return ValidationResult.reject('產生器圖層沒有來源')

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
