from PySide2 import QtGui, QtWidgets  # type: ignore
import substance_painter as sp  # type: ignore

import importlib
import ui.radial_menu as radial_menu
import logic.transform as transform
import logic.randomize as randomize

importlib.reload(radial_menu)
importlib.reload(transform)
importlib.reload(randomize)


def on_menu_option_selected(option):
    if option == "映射變換":
        transform.main()
    elif option == "隨機化種子":
        randomize.main()


parent = sp.ui.get_main_window()
menu = radial_menu.RadialMenu(parent, ["映射變換", "隨機化種子"], on_menu_option_selected)

open_menu_action = QtWidgets.QAction("開啟插件選單", parent)
open_menu_action.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
open_menu_action.triggered.connect(lambda: menu.show_at_cursor())


def start_plugin():
    sp.ui.add_action(sp.ui.ApplicationMenu.Edit, open_menu_action)


def close_plugin():
    global open_menu_action, menu
    sp.ui.delete_ui_element(open_menu_action)
    menu.deleteLater()
