# Substance Painter Tools

## 簡介

本插件提供了兩個實用的 Substance Painter 10.0.1 工具，透過簡潔的徑向選單介面，讓設計師能夠快速進行材質調整：

### 1. 映射變換 (Transform Mapping)

對選定的紋理集執行 UV 映射變換或是參數變換，包括縮放和旋轉調整。

**支援的圖層類型：**
- Fill Layers (填充圖層)
- Fill Effects (填充效果)
- Generator Effects (生成器效果)
- 未來版本將支援 Filter Effects (濾鏡效果)

**功能特點：**
- 批次縮放調整（0.25x - 100x）
- 旋轉角度設定（-180° 到 180°）
- 智能跳過不適用的圖層
- 支援 Split Source 多通道處理
- 自動排除 Anchor 和專案資源類型
- 結束時的完整改動統整對話框

### 2. 隨機化種子 (Randomize Seeds)

快速重設專案中所有包含隨機種子參數的 Substance 材質。

**處理範圍：**
- 填充圖層中的 Substance 材質
- 圖層效果中的 Substance 材質
- 巢狀 Substance 輸入源
- 所有紋理集和堆疊

---

## 安裝指南

1. 下載或複製專案檔案
2. 將整個專案資料夾放入 Substance Painter 的插件目錄：
   ```
   C:\Users\<Your Username>\Documents\Adobe\Adobe Substance 3D Painter\python\plugins
   ```
3. 重啟 Substance Painter

---

## 使用方法

1. 開啟 Substance Painter 專案
2. 按下 `Ctrl+Q` 呼出插件選單
3. 選擇要使用的功能

---

### 相容性

- **Substance Painter 版本**：10.0.1 或更高版本
