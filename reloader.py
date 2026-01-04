import substance_painter as sp  # type: ignore
import importlib
import sys

# 定義需要重載的模組順序 (優先級是 1. package, 2. 底層模組, 3. 高層模組)
# 因為 Python 模組系統的技術限制優先於邏輯依賴，因此 package 放在最前面
# 具體來說，transform.utils 依賴於 transform 包，因此 transform 必須先被重載，即便 transform 是最高層
# 否則會出現 ImportError: parent 'transform' not in sys.modules 的錯誤
MODULES_TO_RELOAD = [
    "transform",
    "transform.utils",
    "transform.handle_fill",
    "transform.handle_generator",
    "randomize",
    "ui.radial_menu",
    "ui.transform_select_dialog",
    "ui.transform_result_dialog",
]


def perform_reload():
    for module_name in MODULES_TO_RELOAD:
        if module_name in sys.modules:
            sp.logging.info(f"Reloading module: {module_name}")
            importlib.reload(sys.modules[module_name])
        else:
            sp.logging.info(f"Importing module: {module_name}")
            importlib.import_module(module_name)
