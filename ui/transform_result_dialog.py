from PySide2 import QtWidgets, QtCore, QtGui  # type: ignore
from typing import Dict


class Dialog(QtWidgets.QDialog):
    def __init__(self, result: Dict[str, Dict], parent=None):
        # 初始化對話框
        super().__init__(parent)
        self.setWindowTitle("變換結果檢視")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        self.result_data = result

        # 統計資料
        self.stats = {"success": 0, "skip": 0, "error": 0}
        self.calculate_stats()

        # 建立UI
        main_layout = QtWidgets.QVBoxLayout(self)
        self.create_filter_options(main_layout)
        self.create_results_table(main_layout)
        self.create_stats_display(main_layout)
        self.create_buttons(main_layout)

        # 初始化篩選
        self.update_table_display()

    def calculate_stats(self):
        """計算統計資料"""
        self.stats = {"success": 0, "skip": 0, "error": 0}
        for path_change in self.result_data.values():
            result_type = path_change.get("type", "error")
            if result_type in self.stats:
                self.stats[result_type] += 1

    def create_filter_options(self, parent_layout):
        """建立篩選選項"""
        filter_group = QtWidgets.QGroupBox("篩選選項")
        filter_layout = QtWidgets.QHBoxLayout()

        # 建立篩選勾選框
        self.filter_checkboxes = {}

        # Success 篩選
        self.filter_checkboxes["success"] = QtWidgets.QCheckBox("✅ 成功")
        self.filter_checkboxes["success"].setChecked(True)
        self.filter_checkboxes["success"].stateChanged.connect(self.update_table_display)
        filter_layout.addWidget(self.filter_checkboxes["success"])

        # Skip 篩選
        self.filter_checkboxes["skip"] = QtWidgets.QCheckBox("⚠️ 跳過")
        self.filter_checkboxes["skip"].setChecked(True)
        self.filter_checkboxes["skip"].stateChanged.connect(self.update_table_display)
        filter_layout.addWidget(self.filter_checkboxes["skip"])

        # Error 篩選
        self.filter_checkboxes["error"] = QtWidgets.QCheckBox("❌ 錯誤")
        self.filter_checkboxes["error"].setChecked(True)
        self.filter_checkboxes["error"].stateChanged.connect(self.update_table_display)
        filter_layout.addWidget(self.filter_checkboxes["error"])

        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        parent_layout.addWidget(filter_group)

    def create_results_table(self, parent_layout):
        """建立結果表格"""
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Path", "LayerType", "Result", "Messages"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)

        # 調整欄位寬度
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)  # Path 欄位可延展
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)  # LayerType 自動調整
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)  # Result 自動調整
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)  # Messages 欄位可延展

        # 允許多行顯示
        self.table.setWordWrap(True)
        self.table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        parent_layout.addWidget(self.table)

    def create_stats_display(self, parent_layout):
        """建立統計顯示"""
        stats_layout = QtWidgets.QHBoxLayout()

        stats_label = QtWidgets.QLabel()
        stats_text = f"統計: ✅ {self.stats['success']} | ⚠️ {self.stats['skip']} | ❌ {self.stats['error']}"
        stats_label.setText(stats_text)
        stats_label.setStyleSheet("font-weight: bold; font-size: 12px; padding: 5px;")

        stats_layout.addWidget(stats_label)
        stats_layout.addStretch()
        parent_layout.addLayout(stats_layout)

    def create_buttons(self, parent_layout):
        """建立底部按鈕"""
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        # 關閉按鈕
        close_button = QtWidgets.QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        parent_layout.addLayout(button_layout)

    def get_result_display_text(self, result_type: str) -> tuple[str, QtGui.QColor]:
        """取得結果顯示文字和顏色"""
        if result_type == "success":
            return "✅ 成功", QtGui.QColor(0, 128, 0)  # 綠色
        elif result_type == "skip":
            return "⚠️ 跳過", QtGui.QColor(255, 140, 0)  # 橙色/黃色
        elif result_type == "error":
            return "❌ 錯誤", QtGui.QColor(220, 20, 60)  # 紅色
        else:
            return "❓ 未知", QtGui.QColor(128, 128, 128)  # 灰色

    def update_table_display(self):
        """更新表格顯示"""
        # 取得篩選狀態
        show_types = set()
        for result_type, checkbox in self.filter_checkboxes.items():
            if checkbox.isChecked():
                show_types.add(result_type)

        # 篩選資料
        filtered_data = {
            path: path_change
            for path, path_change in self.result_data.items()
            if path_change.get("type", "error") in show_types
        }

        # 更新表格
        self.table.setRowCount(len(filtered_data))

        for row, (path, path_change) in enumerate(filtered_data.items()):
            # Path 欄位
            path_item = QtWidgets.QTableWidgetItem(path)
            path_item.setFlags(path_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 0, path_item)

            # LayerType 欄位
            layer_type = path_change.get("layer_type", "Unknown")
            layer_type_item = QtWidgets.QTableWidgetItem(layer_type)
            layer_type_item.setFlags(layer_type_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 1, layer_type_item)

            # Result 欄位
            result_type = path_change.get("type", "error")
            result_text, result_color = self.get_result_display_text(result_type)
            result_item = QtWidgets.QTableWidgetItem(result_text)
            result_item.setFlags(result_item.flags() & ~QtCore.Qt.ItemIsEditable)
            result_item.setForeground(result_color)
            self.table.setItem(row, 2, result_item)

            # Messages 欄位
            messages = path_change.get("messages", [])
            messages_text = "\n".join(messages) if messages else ""
            messages_item = QtWidgets.QTableWidgetItem(messages_text)
            messages_item.setFlags(messages_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 3, messages_item)

        # 調整行高以適應內容
        self.table.resizeRowsToContents()
