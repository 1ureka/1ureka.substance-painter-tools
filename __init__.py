from PySide2 import QtGui, QtWidgets  # type: ignore
import substance_painter as sp  # type: ignore
import sys
from pathlib import Path


plugin_path = str(Path(__file__).parent)
open_menu_action = None
menu = None


def prepare_modules():
    """
    配置插件環境變數並將插件路徑加入系統路徑。

    確保 Python 解釋器能正確找到插件目錄下的自定義模組 (如 ui, transform 等) 。
    """
    if plugin_path not in sys.path:
        sys.path.append(plugin_path)
        sp.logging.info("已將插件路徑加入 sys.path")
        sp.logging.info(f"路徑: {plugin_path}")


def cleanup_modules():
    """
    清理已載入的模組快取並還原系統路徑。

    遍歷 sys.modules 並刪除指定的插件模組 (ui, transform, randomize)
    確保下次啟動插件時會重新讀取檔案而非使用記憶體中的舊版本。
    """
    prefixes = ["ui", "transform", "randomize"]
    to_delete = [m for m in sys.modules if any(m.startswith(p) for p in prefixes)]

    for m in to_delete:
        del sys.modules[m]

    sp.logging.info(f"已清理模組快取: {', '.join(to_delete)}")

    if plugin_path in sys.path:
        sys.path.remove(plugin_path)
        sp.logging.info("已從 sys.path 移除插件路徑")
        sp.logging.info(f"路徑: {plugin_path}")


def start_plugin():
    """
    Substance Painter 插件啟動入口。

    執行流程:
    1. 初始化模組路徑。
    2. 動態匯入 UI 與功能模組。
    3. 初始化徑向選單 (Radial Menu) 並綁定回呼函式。
    4. 在 Substance Painter 的「編輯 (Edit)」選單中建立快捷鍵入口 (Ctrl+Q)。
    """
    global open_menu_action, menu

    prepare_modules()

    from ui.radial_menu import RadialMenu
    import transform
    import randomize

    def on_menu_option_selected(option):
        if option == "映射變換":
            transform.main()
        elif option == "隨機化種子":
            randomize.main()

    parent = sp.ui.get_main_window()
    menu = RadialMenu(parent, ["映射變換", "隨機化種子"], on_menu_option_selected)

    open_menu_action = QtWidgets.QAction("開啟插件選單", parent)
    open_menu_action.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
    open_menu_action.triggered.connect(lambda: menu.show_at_cursor())

    sp.ui.add_action(sp.ui.ApplicationMenu.Edit, open_menu_action)


def close_plugin():
    """
    Substance Painter 插件關閉與資源釋放。

    執行流程:
    1. 從 Substance Painter UI 選單中移除動作物件。
    2. 銷毀徑向選單實例並標記資源釋放。
    3. 呼叫 cleanup_modules 清理 Python 環境變數。
    """
    global open_menu_action, menu

    if open_menu_action:
        sp.ui.delete_ui_element(open_menu_action)
        open_menu_action = None

    if menu:
        menu.destroyed.connect(lambda: sp.logging.info("已正確釋放插件選單資源"))
        menu.deleteLater()
        menu = None

    cleanup_modules()
