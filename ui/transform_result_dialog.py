from PySide2 import QtWidgets, QtCore, QtGui  # type: ignore
from typing import Dict, Tuple, Optional
from transform.utils import DispatchResults


def generate_markdown(results: DispatchResults, scale: float, rotation: float) -> str:
    from datetime import datetime

    lines = []
    lines.append("# 映射變換執行日誌\n")
    lines.append(f"**執行時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**變換參數**: 縮放 = {scale}x, 旋轉 = {rotation}°\n")
    lines.append("---\n")

    # 統計
    success_count = sum(1 for r in results.values() if r.status)
    fail_count = sum(1 for r in results.values() if not r.status)
    lines.append("## 統計資訊\n")
    lines.append(f"- ✓ **成功**: {success_count}")
    lines.append(f"- ✗ **失敗**: {fail_count}")
    lines.append(f"- **總計**: {len(results)}\n")
    lines.append("---\n")

    # 成功項目
    if success_count > 0:
        lines.append("## ✓ 成功項目\n")
        for layer_path, result in results.items():
            if result.status:
                lines.append(f"### {result.title}")
                lines.append(f"**路徑**: {' > '.join(layer_path)}")
                lines.append(f"> {result.detail}\n")
        lines.append("---\n")

    # 失敗項目
    if fail_count > 0:
        lines.append("## ✗ 失敗項目\n")
        for layer_path, result in results.items():
            if not result.status:
                lines.append(f"### {result.title}")
                lines.append(f"**路徑**: {' > '.join(layer_path)}")
                lines.append(f"> {result.detail}\n")

    return "\n".join(lines)


class TreeLogDialog(QtWidgets.QDialog):
    def __init__(self, results: DispatchResults, scale: float, rotation: float, parent=None):
        super().__init__(parent)

        self.results = results
        self.scale = scale
        self.rotation = rotation

        self.setWindowTitle("變換結果檢視")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)

        # 主要佈局
        main_layout = QtWidgets.QVBoxLayout(self)

        # 1. 篩選選項
        self.create_filter_options(main_layout)

        # 2. 樹狀列表 (QTreeWidget)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["名稱 / 路徑", "詳細資訊"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.tree.setFocusPolicy(QtCore.Qt.NoFocus)
        main_layout.addWidget(self.tree)

        # 3. 初始化樹狀數據
        self.build_tree_structure()
        self.tree.expandAll()  # 預設展開所有節點

        # 4. Markdown 預覽按鈕或底部操作
        self.create_bottom_buttons(main_layout)

    def create_filter_options(self, parent_layout):
        filter_group = QtWidgets.QGroupBox("篩選選項")
        filter_layout = QtWidgets.QHBoxLayout()

        self.filter_success = QtWidgets.QCheckBox("✓ 成功")
        self.filter_success.setChecked(True)
        self.filter_success.stateChanged.connect(self.update_tree_display)

        self.filter_fail = QtWidgets.QCheckBox("✗ 失敗")
        self.filter_fail.setChecked(True)
        self.filter_fail.stateChanged.connect(self.update_tree_display)

        filter_layout.addWidget(self.filter_success)
        filter_layout.addWidget(self.filter_fail)
        filter_layout.addStretch()

        filter_group.setLayout(filter_layout)
        parent_layout.addWidget(filter_group)

    def create_bottom_buttons(self, parent_layout):
        btn_layout = QtWidgets.QHBoxLayout()

        self.copy_md_btn = QtWidgets.QPushButton("複製 Markdown 日誌")
        self.copy_md_btn.clicked.connect(self.copy_to_clipboard)

        self.close_btn = QtWidgets.QPushButton("關閉")
        self.close_btn.clicked.connect(self.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(self.copy_md_btn)
        btn_layout.addWidget(self.close_btn)
        parent_layout.addLayout(btn_layout)

    def copy_to_clipboard(self):
        md_text = generate_markdown(self.results, self.scale, self.rotation)
        QtWidgets.QApplication.clipboard().setText(md_text)
        QtWidgets.QMessageBox.information(self, "成功", "Markdown 日誌已複製到剪貼簿！")

    def get_status_icon_and_color(self, status: bool) -> Tuple[str, QtGui.QColor]:
        if status:
            return "✓", QtGui.QColor(0, 128, 0).lighter(130)
        else:
            return "✗", QtGui.QColor(220, 20, 60).lighter(170)

    def build_tree_structure(self):
        path_nodes: Dict[Tuple[str, ...], QtWidgets.QTreeWidgetItem] = {}

        for layer_path, result in self.results.items():
            # 建立父層級路徑節點
            for i in range(len(layer_path)):
                partial_path = layer_path[: i + 1]

                if partial_path not in path_nodes:
                    if i == 0:
                        node = QtWidgets.QTreeWidgetItem(self.tree)
                        node.setText(0, layer_path[i])
                    else:
                        parent_path = layer_path[:i]
                        parent_node = path_nodes[parent_path]
                        node = QtWidgets.QTreeWidgetItem(parent_node)
                        node.setText(0, layer_path[i])

                    # 給父節點一個灰色字體，區別於結果節點
                    node.setForeground(0, QtGui.QColor("#ffffffaa"))
                    path_nodes[partial_path] = node

            # 添加最終結果節點
            parent_node = path_nodes[layer_path]
            result_node = QtWidgets.QTreeWidgetItem(parent_node)

            icon, color = self.get_status_icon_and_color(result.status)
            result_node.setText(0, f"{icon} {result.title}")
            result_node.setText(1, result.detail)
            result_node.setForeground(0, color)
            # 存儲狀態以便後續篩選
            result_node.setData(0, QtCore.Qt.UserRole, result.status)

    def update_tree_display(self):
        show_success = self.filter_success.isChecked()
        show_fail = self.filter_fail.isChecked()

        # 先收集所有項目到列表中 (避免在遍歷時修改導致 iterator 失效)
        all_items = []
        iterator = QtWidgets.QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            all_items.append(iterator.value())
            iterator += 1

        # 先隱藏所有節點
        for item in all_items:
            item.setHidden(True)

        # 收集需要顯示的結果節點
        visible_result_items = []
        for item in all_items:
            status = item.data(0, QtCore.Qt.UserRole)

            # 檢查這是否為結果節點 (UserRole 存有 True/False)
            if status is not None:
                is_visible = (status and show_success) or (not status and show_fail)
                if is_visible:
                    visible_result_items.append(item)

        # 顯示需要顯示的節點及其所有祖先節點
        for item in visible_result_items:
            current = item
            while current is not None:
                current.setHidden(False)
                current = current.parent()


def show_transform_results(results: DispatchResults, scale: float, rotation: float, parent=None) -> None:
    dialog: Optional[TreeLogDialog] = None

    try:
        dialog = TreeLogDialog(results, scale, rotation, parent)
        dialog.exec_()  # 執行對話框 (此處會阻塞直到使用者關閉視窗)

    except Exception as e:
        QtWidgets.QMessageBox.critical(parent, "錯誤", f"無法開啟結果檢視器: \n{str(e)}")

    finally:
        if dialog:
            dialog.deleteLater()
