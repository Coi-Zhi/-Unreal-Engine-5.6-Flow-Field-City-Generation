# -Unreal-Engine-5.6-Flow-Field-City-Generation

<img width="414" height="283" alt="屏幕截图 2026-04-30 231410" src="https://github.com/user-attachments/assets/ab2acf62-39a2-4999-9fb5-586af130b7d4" />

<img width="410" height="280" alt="屏幕截图 2026-04-30 231432" src="https://github.com/user-attachments/assets/b6599796-f482-4cd6-a76d-d8a9f99bcdf5" />


# UE5 Procedural City Generator Plugin

[English Version Below](#english-version)

## 專案簡介 (Overview)
這是一個基於 Unreal Engine 5 Python API 開發的程序化城市生成插件 (Editor Utility Plugin)。本插件解決了傳統藍圖生成大量 Actor 時的效能瓶頸，透過底層 HISM (Hierarchical Instanced Static Mesh) 與自定義空間演算法，實現 10 萬棟以上建築級別的瞬間生成與無縫局部刷新。

## 核心特性 (Core Features)
*   **極限效能 (HISM & SubobjectDataSubsystem)**
    全面改用 HISM 來取代傳統的 Actor 生成。為了確保在 Python 中動態添加組件能完美支援編輯器存檔 (Ctrl+S) 與 Undo/Redo，系統採用了 UE5 官方最高權限的 SubobjectDataSubsystem，避免內存遺失與崩潰。
*   **O(1) 空間重疊剔除 (Spatial Hash Grid)**
    實作了自定義的空間雜湊網格演算法。將生成區域劃分為多個 Grid Cells，在生成新建築前進行局部比對，將重疊檢測的時間複雜度由 O(N^2) 降至均攤 O(1)，極大化處理速度。
*   **無縫局部刷新 (Eraser Bounding Box)**
    引入「橡皮擦模式」。透過提取新輸入點集的極值建立一個大範圍 Bounding Box，在生成新建築前，瞬間強拆範圍內的舊有實例。這保證了地塊的絕對純淨，讓新舊城區無縫接合。
*   **幾何流場與地塊分割 (Flow Field & Shapely)**
    利用向量流場演算法計算干擾點，生成具備自然有機感的城市道路網。隨後利用開源幾何庫 Shapely 將路網精確切割為獨立地塊，並向內縮進計算出可建築的安全區域。
*   **精準地形貼合 (Raycast Sequencing)**
    嚴格控制執行順序：先清空舊實例碰撞，再發射 Z 軸射線進行地形測高，最後實例化新建築。這避免了射線誤擊舊有建築屋頂的問題，確保 100% 準確降落於真實地表。

## 系統需求與安裝 (Requirements & Installation)
1.  **Unreal Engine**: 5.x 版本
2.  **安裝插件**: 將本插件資料夾放入 UE 專案根目錄下的 `Plugins/` 資料夾中。
3.  **安裝 Python 依賴**: 本插件依賴 `Shapely` 庫。請在 UE 的 Python 環境中安裝：
    *   導航至: `C:\Program Files\Epic Games\UE_5.x\Engine\Binaries\ThirdParty\Python3\Win64`
    *   執行指令: `python.exe -m pip install shapely`

## 快速開始 (Quick Start)
1.  在 Content Browser 中找到本插件提供的 Editor Utility Widget (EUW)，右鍵選擇 **Run Editor Utility Widget**。
2.  在 EUW 面板中設定道路寬度、密度、Seed 等參數。
3.  點擊 **Bound_Update** 進行範圍繪製，點擊**Select Bound**后能對這個範圍進行移動，之後記得再次點解**Bound_Update**更新位置。
4.  點擊 **Generate** 即可瞬間生成城市。

---

# English Version

## Overview
This is a Procedural City Generation Plugin for Unreal Engine 5, built using the UE5 Python API and Editor Utility Widgets (EUW). It overcomes the performance bottlenecks of traditional Blueprint-based Actor spawning. By utilizing Hierarchical Instanced Static Meshes (HISM) and custom spatial algorithms, it achieves instantaneous generation and seamless local updates for massive-scale cities (100,000+ building instances).

## Core Features
*   **Extreme Performance (HISM & SubobjectDataSubsystem)**
    Replaces traditional Actor spawning with HISM. To ensure dynamic components added via Python support editor saving (Ctrl+S) and Undo/Redo securely, the tool utilizes UE5's SubobjectDataSubsystem. This prevents data loss and editor crashes.
*   **O(1) Spatial Culling (Spatial Hash Grid)**
    Implements a custom Spatial Hash Grid algorithm. By dividing the generation area into grid cells, the system performs local intersection checks before spawning new buildings. This reduces the time complexity of overlap detection from O(N^2) to an amortized O(1).
*   **Seamless Wipe & Redraw (Eraser Bounding Box)**
    Introduces a "Cookie-Cutter" or Eraser mode. The system calculates a global bounding box based on the min/max values of the new input points. It instantly clears all old instances within this box before spawning new ones, ensuring clean parcels and seamless blending between old and new city blocks.
*   **Flow Field & Parcel Partitioning (Shapely)**
    Generates organic, natural-looking road networks using a vector flow field algorithm. The open-source geometry library Shapely is then used to precisely partition the road network into independent parcels and calculate safe building zones via polygon buffering.
*   **Accurate Terrain Snapping (Raycast Sequencing)**
    Strictly manages the execution pipeline: it first clears the collision of old instances, then performs Z-axis raycasting for terrain height detection, and finally spawns the new buildings. This prevents raycasts from hitting old rooftops, ensuring 100% accurate snapping to the landscape.

## Requirements & Installation
1.  **Unreal Engine**: Version 5.x
2.  **Plugin Installation**: Place the plugin folder into the `Plugins/` directory of your Unreal Engine project.
3.  **Python Dependencies**: This plugin requires the `Shapely` library. Install it in your UE Python environment:
    *   Navigate to: `C:\Program Files\Epic Games\UE_5.x\Engine\Binaries\ThirdParty\Python3\Win64`
    *   Run command: `python.exe -m pip install shapely`

## Quick Start
1.  Locate the Editor Utility Widget (EUW) provided by the plugin in the Content Browser, right-click, and select **Run Editor Utility Widget**.
2.  Adjust parameters such as road width, density, and Seed in the EUW panel.
3.  Clik **Bound_Update** to draw the Spline of Area, Clik **Select Bound** to adjusting the location, after that remember the Clik the **Bound_Update** again to update the location.
4.  Click **Generate** to instantly spawn your procedural city.
