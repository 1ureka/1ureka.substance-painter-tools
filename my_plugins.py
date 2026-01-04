from PySide2 import QtGui, QtWidgets  # type: ignore
import substance_painter as sp  # type: ignore
import sys

open_menu_action = None
menu = None


def cleanup_modules():
    """清理所有屬於此插件路徑下的模組快取"""
    # TODO: 都改成在一個特定的包目錄下（例如 'my_plugin_folder'），因此該檔案要改名為 __init__.py 並放在 my_plugin_folder 目錄下
    prefixes = ["ui", "transform", "randomize"]

    # 找出所有符合前綴的模組 key
    to_delete = [m for m in sys.modules if any(m.startswith(p) for p in prefixes)]

    for m in to_delete:
        del sys.modules[m]

    sp.logging.info(f"已清理模組快取: {', '.join(to_delete)}")


def start_plugin():
    global open_menu_action, menu

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
    global open_menu_action, menu

    if open_menu_action:
        sp.ui.delete_ui_element(open_menu_action)
        open_menu_action = None

    if menu:
        menu.destroyed.connect(lambda: sp.logging.info("已正確釋放插件選單資源"))
        menu.deleteLater()
        menu = None

    cleanup_modules()
