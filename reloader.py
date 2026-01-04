import substance_painter as sp  # type: ignore
import importlib
import sys

# 定義需要重載的模組順序（由底層到高層）
MODULES_TO_RELOAD = [
    "transform.utils",
    "transform.handle_fill",
    "transform.handle_generator",
    "transform",
    "randomize",
    "ui.transform_select_dialog",
    "ui.transform_result_dialog",
    "ui.radial_menu",
]


def perform_reload():
    for module_name in MODULES_TO_RELOAD:
        if module_name in sys.modules:
            sp.logging.info(f"Reloading module: {module_name}")
            importlib.reload(sys.modules[module_name])
        else:
            # 如果模組還沒被載入過，就直接 import 它
            importlib.import_module(module_name)
