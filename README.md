# Substance Painter 插件套件 / Substance Painter Tools

[中文版本](#簡介) | [English Version](#introduction)

---

### 簡介

這是一組基於 **Adobe Substance 3D Painter 10.0.1** API 與 **PySide2** 開發的實用插件，提供紋理處理自動化功能與快捷選單介面，讓素材編輯與隨機化更高效。

---

### 功能特色

#### 核心功能

* **映射變換（Transform）**
  批量調整所選紋理集的 UV 縮放與旋轉，支援 **UV** 與 **Triplanar** 投影模式，並能自動過濾不可縮放來源（例如 Anchor、部分程序化材質）。

* **隨機化種子（Randomize Seed）**
  自動搜尋專案內所有支援 `$randomseed` 參數的來源，並一次性替換為新的隨機值，讓程序化材質的結果快速多樣化。

* **快捷圓形選單（Radial Menu）**
  以 `Ctrl+Q` 快捷鍵呼出圓形選單，快速選擇要執行的功能（映射變換 / 隨機化種子）。

---

### 安裝與使用

#### 1️⃣ 安裝

1. 將整個專案放入 **Substance Painter 插件資料夾**（通常位於
   `C:\Users\<你的使用者名稱>\Documents\Adobe\Adobe Substance 3D Painter\python\plugins`）。
2. 確保專案結構如下：

   ```
   logic/
       transform.py
       randomize.py
   ui/
       radial_menu.py
       texture_sets_select.py
   my_plugins.py
   ```
3. 重新啟動 **Substance Painter**。

#### 2️⃣ 使用

1. 開啟任意專案並載入材質。
2. 按下 `Ctrl+Q` 呼出插件圓形選單。
3. 選擇：

   * **映射變換** → 彈出對話框設定縮放倍數與旋轉角度，勾選需處理的 Texture Set。
   * **隨機化種子** → 自動搜尋並替換所有支援隨機種子的來源。

---

### Introduction

This is a set of practical plugins for **Adobe Substance 3D Painter 10.0.1**, developed using its Python API and **PySide2**. It provides automation for texture processing and a quick-access radial menu, making editing and randomization faster and more efficient.

---

### Features

#### Core Functions

* **Transform**
  Batch-adjust the UV scale and rotation of selected texture sets, supporting **UV** and **Triplanar** projection modes, while automatically filtering out non-scalable sources (e.g., Anchors, certain procedural materials).

* **Randomize Seed**
  Automatically scans all sources in the project that support the `$randomseed` parameter and replaces them with a new random value, quickly diversifying procedural material results.

* **Radial Menu**
  Trigger a radial menu with `Ctrl+Q` to quickly select an action (Transform / Randomize Seed).

---

### Installation & Usage

#### 1️⃣ Installation

1. Place the entire project folder into the **Substance Painter plugins directory** (usually located at
   `C:\Users\<Your Username>\Documents\Adobe\Adobe Substance 3D Painter\python\plugins`).
2. Ensure the project structure is as follows:

   ```
   logic/
       transform.py
       randomize.py
   ui/
       radial_menu.py
       texture_sets_select.py
   my_plugins.py
   ```
3. Restart **Substance Painter**.

#### 2️⃣ Usage

1. Open any project and load materials.
2. Press `Ctrl+Q` to open the radial menu.
3. Select:

   * **Transform** → A dialog will appear to set scaling and rotation, and select the Texture Sets to process.
   * **Randomize Seed** → Automatically scans and replaces all supported random seeds.
