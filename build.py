import shutil
from pathlib import Path


def build_plugin():
    """
    建置並複製插件檔案到目標目錄。

    此函數會：
    1. 找出專案根目錄下所有的 .py 檔案（遞迴）
    2. 複製到目標目錄，並包裝在 1ureka_tools 子目錄中
    3. 保持原有的目錄結構
    """
    # 專案根目錄（當前腳本所在目錄）
    project_root = Path(__file__).parent

    # 目標目錄（Substance Painter 插件目錄）
    target_base = Path(r"C:\\Users\\Summe\\Documents\\Adobe\\Adobe Substance 3D Painter\\python\\plugins")

    # 插件在目標目錄中的包名稱
    plugin_folder_name = "1ureka_tools"

    # 完整目標路徑
    target_dir = target_base / plugin_folder_name

    print(f"專案根目錄: {project_root}")
    print(f"目標目錄: {target_dir}")
    print("-" * 60)

    # 如果目標目錄已存在，先清空
    if target_dir.exists():
        print(f"清空現有目標目錄: {target_dir}")
        shutil.rmtree(target_dir)

    # 建立目標目錄
    target_dir.mkdir(parents=True, exist_ok=True)

    # 遍歷專案根目錄下的所有檔案
    copied_files = []
    for file_path in project_root.rglob("*.py"):
        # 排除 build.py 自身
        if file_path.name == "build.py":
            continue

        relative_path = file_path.relative_to(project_root)
        target_file = target_dir / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # 複製檔案
        shutil.copy2(file_path, target_file)
        copied_files.append(relative_path)
        print(f"✓ 已複製: {relative_path}")

    print("-" * 60)
    print(f"建置完成！共複製 {len(copied_files)} 個檔案")
    print(f"插件位置: {target_dir}")


if __name__ == "__main__":
    try:
        build_plugin()
    except Exception as e:
        print(f"建置失敗: {e}")
        raise
