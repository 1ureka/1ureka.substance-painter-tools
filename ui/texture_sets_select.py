from PySide2 import QtWidgets, QtCore  # type: ignore
from typing import List


class Row:
    def __init__(self, name: str):
        self.name = name
        self.selected = True


class Result:
    def __init__(self, scale: float, rotation: int, texture_sets: List[str]):
        self.scale = scale
        self.rotation = rotation
        self.texture_sets = texture_sets


class Dialog(QtWidgets.QDialog):
    def __init__(self, rows: List[Row], parent=None):
        super().__init__(parent)
        self.rows = rows
        self.scale = 2.0
        self.rotation = 0
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("選擇需映射變換的紋理集")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)

        # 佈局
        main_layout = QtWidgets.QVBoxLayout(self)
        self.create_top_options(main_layout)
        self.create_layer_list(main_layout)
        self.create_buttons(main_layout)

    def create_top_options(self, parent_layout):
        """建立頂部選項區域"""
        top_widget = QtWidgets.QWidget()
        top_layout = QtWidgets.QVBoxLayout(top_widget)

        # 創建主要選項的水平佈局
        main_options_layout = QtWidgets.QHBoxLayout()

        # 縮放區域
        scale_group = QtWidgets.QGroupBox("縮放倍數")
        scale_layout = QtWidgets.QVBoxLayout(scale_group)

        # 縮放輸入欄
        scale_input_layout = QtWidgets.QHBoxLayout()
        self.scale_spinbox = QtWidgets.QDoubleSpinBox()
        self.scale_spinbox.setRange(0.01, 100.0)
        self.scale_spinbox.setDecimals(2)
        self.scale_spinbox.setValue(self.scale)
        self.scale_spinbox.valueChanged.connect(self.on_scale_changed)
        scale_input_layout.addWidget(self.scale_spinbox)
        scale_input_layout.addStretch()
        scale_layout.addLayout(scale_input_layout)

        # 縮放快速選取按鈕
        scale_buttons_widget = QtWidgets.QWidget()
        scale_buttons_layout = QtWidgets.QHBoxLayout(scale_buttons_widget)
        scale_buttons_layout.setContentsMargins(0, 0, 0, 0)
        scale_values = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2]
        for value in scale_values:
            btn = QtWidgets.QPushButton(str(value))
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda _=None, v=value: self.scale_spinbox.setValue(v))
            scale_buttons_layout.addWidget(btn)
        scale_buttons_layout.addStretch()
        scale_layout.addWidget(scale_buttons_widget)

        # 旋轉區域
        rotation_group = QtWidgets.QGroupBox("旋轉度數")
        rotation_layout = QtWidgets.QVBoxLayout(rotation_group)

        # 旋轉輸入欄
        rotation_input_layout = QtWidgets.QHBoxLayout()
        self.rotation_spinbox = QtWidgets.QSpinBox()
        self.rotation_spinbox.setRange(-180, 180)
        self.rotation_spinbox.setSingleStep(90)
        self.rotation_spinbox.setValue(self.rotation)
        self.rotation_spinbox.valueChanged.connect(self.on_rotation_changed)
        rotation_input_layout.addWidget(self.rotation_spinbox)
        rotation_input_layout.addStretch()
        rotation_layout.addLayout(rotation_input_layout)

        # 旋轉快速選取按鈕
        rotation_buttons_widget = QtWidgets.QWidget()
        rotation_buttons_layout = QtWidgets.QHBoxLayout(rotation_buttons_widget)
        rotation_buttons_layout.setContentsMargins(0, 0, 0, 0)
        rotation_values = [-180, -90, 0, 90, 180]
        for value in rotation_values:
            btn = QtWidgets.QPushButton(str(value) + "°")
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda _=None, v=value: self.rotation_spinbox.setValue(v))
            rotation_buttons_layout.addWidget(btn)
        rotation_buttons_layout.addStretch()
        rotation_layout.addWidget(rotation_buttons_widget)

        # 將縮放和旋轉區域加入主要選項佈局
        main_options_layout.addWidget(scale_group)
        main_options_layout.addWidget(rotation_group)
        main_options_layout.addStretch()

        top_layout.addLayout(main_options_layout)
        parent_layout.addWidget(top_widget)

    def create_layer_list(self, parent_layout):
        """建立列表區域"""
        # 全選/全不選按鈕區域
        select_buttons_layout = QtWidgets.QHBoxLayout()

        select_all_button = QtWidgets.QPushButton("全選")
        select_all_button.clicked.connect(self.create_on_select_all(True))
        select_buttons_layout.addWidget(select_all_button)

        deselect_all_button = QtWidgets.QPushButton("全不選")
        deselect_all_button.clicked.connect(self.create_on_select_all(False))
        select_buttons_layout.addWidget(deselect_all_button)

        select_buttons_layout.addStretch()
        parent_layout.addLayout(select_buttons_layout)

        # 創建表格
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["選擇", "紋理集"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(False)

        # 填充表格資料
        self.populate_table()

        # 調整欄位寬度
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        parent_layout.addWidget(self.table)

    def populate_table(self):
        """填充表格資料"""
        self.table.setRowCount(len(self.rows))

        for i, row in enumerate(self.rows):
            # 選擇欄 (checkbox)
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(row.selected)
            checkbox.stateChanged.connect(lambda state, r=i: self.on_selection_changed(r, state))
            self.table.setCellWidget(i, 0, checkbox)

            # 紋理集名稱
            item1 = QtWidgets.QTableWidgetItem(row.name)
            item1.setFlags(item1.flags() & ~QtCore.Qt.ItemIsEditable)  # 禁止編輯
            self.table.setItem(i, 1, item1)

    def create_buttons(self, parent_layout):
        """建立底部按鈕"""
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        # 套用按鈕
        apply_button = QtWidgets.QPushButton("套用所選變換")
        apply_button.clicked.connect(self.on_submit)
        button_layout.addWidget(apply_button)

        # 取消按鈕
        cancel_button = QtWidgets.QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        parent_layout.addLayout(button_layout)

    def on_scale_changed(self, value):
        self.scale = value

    def on_rotation_changed(self, value):
        self.rotation = value

    def create_on_select_all(self, checked):
        def fn():
            for i in range(self.table.rowCount()):
                checkbox = self.table.cellWidget(i, 0)
                if checkbox:
                    checkbox.setChecked(checked)

        return fn

    def on_selection_changed(self, i, state):
        self.rows[i].selected = state == QtCore.Qt.Checked

    def on_submit(self):
        texture_sets = [row.name for row in self.rows if row.selected]

        if not texture_sets:
            QtWidgets.QMessageBox.warning(self, "警告", "請至少選擇一個紋理集進行映射變換。")
            return

        self.result = Result(self.scale, self.rotation, texture_sets)
        self.accept()
