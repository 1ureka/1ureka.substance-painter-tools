from PySide2 import QtGui, QtWidgets
import substance_painter as sp

import importlib
import ui.radial_menu as radial_menu
import logic.transform as transform
import logic.randomize as randomize

importlib.reload(radial_menu)
importlib.reload(transform)
importlib.reload(randomize)

WIDGETS = []


def on_menu_option_selected(option):
    if option == "映射變換":
        transform.main()
    elif option == "隨機化種子":
        randomize.main()


def start_plugin():
    parent = sp.ui.get_main_window()

    menu = radial_menu.RadialMenu(parent, ["映射變換", "隨機化種子"], on_menu_option_selected)
    WIDGETS.append(menu)

    action = QtWidgets.QAction("開啟插件選單", parent)
    action.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
    action.triggered.connect(lambda: menu.show_at_cursor())

    sp.ui.add_action(sp.ui.ApplicationMenu.Edit, action)
    WIDGETS.append(action)


def close_plugin():
    for widget in WIDGETS:
        sp.ui.delete_ui_element(widget)
