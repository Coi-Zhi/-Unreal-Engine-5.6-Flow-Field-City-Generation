# -Unreal-Engine-5.6-Flow-Field-City-Generation
<img width="414" height="283" alt="屏幕截图 2026-04-30 231410" src="https://github.com/user-attachments/assets/ab2acf62-39a2-4999-9fb5-586af130b7d4" />

---

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
*   **自定義建築群組 (Data-Driven Theme Configuration)**
    引入基於 Struct 與 Data Asset 的資料驅動工作流。美術人員無需修改程式碼，即可透過 UMG 面板無縫切換不同的城市主題。系統支援精細控制單一建築模型的生成權重 (Weight)、種類配置與幾何變形 (Scale/Z-Offset)，大幅提升迭代效率與資產管理的靈活性。
*   **非阻塞異步架構 (Asynchronous Processing & Non-Blocking UI)**
    徹底重構底層執行邏輯，將高密度的幾何運算（如 Flow Field 計算與 Shapely 地塊分割）全數剝離至背景執行緒 (Background Thread) 執行。生成大型城市時，Unreal Engine 編輯器將保持絕對流暢，徹底告別卡頓與「無回應」狀態。
*   **實時進度回饋 (Real-time Progress Synchronization)**
    建立跨執行緒的安全通訊橋樑。透過藍圖 Timer Handle 機制精準監控背景運算，使用者可在 UMG 控制面板上即時查看當前計算階段與進度條 (Progress Bar)，提供極致順暢的工具交互體驗。
*   **極限執行緒安全與存檔支援 (Thread-Safe Instantiation)**
    嚴格劃分運算與渲染邊界：背景執行緒僅處理純粹的數據演算，待資料備妥後，系統會精準切換回主執行緒 (Main Thread) 執行 HISM 生成與射線檢測。這不僅杜絕了跨執行緒呼叫 UE 引擎造成的崩潰風險，更完美保留了編輯器的 Undo/Redo (Ctrl+Z) 功能。

## 系統需求與安裝 (Requirements & Installation)
1.  **Unreal Engine**: 5.x 版本
2.  **安裝插件**: 將本插件資料夾放入 UE 專案根目錄下的 `Plugins/` 資料夾中。
3.  **安裝 Python 依賴**: 本插件依賴 `Shapely` 庫。請在 UE 的 Python 環境中安裝：
    *   導航至: `C:\Program Files\Epic Games\UE_5.x\Engine\Binaries\ThirdParty\Python3\Win64`
    *   執行指令: `python.exe -m pip install shapely`

## 快速開始 (Quick Start)
1.  **開啟工具**：在 Content Browser 中找到本插件提供的 Editor Utility Widget (EUW)，右鍵選擇 **Run Editor Utility Widget**。
2.  **配置城市主題 (Data Asset)**：
    *   在插件資料夾內找到預設的 Data Asset (例如 `DA_DefaultTheme`) 並雙擊打開。
    *   在 `Buildings` 陣列中，將預設的 Static Mesh 替換為你自己的建築模型。
    *   你可以在此自定義每一棟建築的生成權重 (Weight) 與縮放範圍，完成後點擊 Save。
3.  **繪製生成範圍**：
    *   點擊 EUW 面板上的 **Bound_Update** 進行範圍繪製。
    *   點擊 **Select Bound** 後，可以在場景中移動或旋轉這個範圍框。調整完畢後，**務必再次點擊 Bound_Update** 以更新底層座標數據。
4.  **設定參數與生成**：
    *   在 EUW 面板中，將剛才配置好的 Data Asset 拖曳至 `Theme Data` 欄位。
    *   設定道路寬度、密度、Seed 等全域參數。
    *   點擊 **Generate** 即可瞬間生成你的專屬城市！
<img width="1105" height="578" alt="屏幕截图 2026-05-01 194612" src="https://github.com/user-attachments/assets/a2510886-f659-4827-be19-65ca84f76e9a" />
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
*   **Custom Building Themes (Data-Driven Configuration)**
    Introduces a Data Asset and Struct-based workflow for artist-friendly customization. Users can seamlessly switch between different city themes via the UMG panel without writing code. The system allows precise control over individual building meshes, including their spawn probabilities (weights), scale ranges, and Z-axis offsets, maximizing asset management flexibility and iteration speed.
*   **Asynchronous Processing & Non-Blocking UI**
    Completely refactored the underlying architecture to offload heavy mathematical computations (e.g., Flow Field processing and Shapely parcel partitioning) to a background thread. The Unreal Engine editor remains completely responsive during large-scale city generation, eliminating freezes and "Not Responding" states.
*   **Real-time Progress Feedback**
    Established a safe cross-thread communication bridge. Using a Blueprint Timer Handle mechanism to monitor background tasks, users can view real-time status updates and progress bar completion directly on the UMG dashboard, delivering a premium user experience.
*   **Thread-Safe Instantiation & Undo Support**
    Strictly delineated computation from rendering: the background thread handles pure data processing, while the final layout is securely handed off to the Main Thread for HISM spawning and raycasting. This eliminates crash risks associated with thread-unsafe UE API calls and flawlessly preserves editor Undo/Redo (Ctrl+Z) functionality.

## Requirements & Installation
1.  **Unreal Engine**: Version 5.x
2.  **Plugin Installation**: Place the plugin folder into the `Plugins/` directory of your Unreal Engine project.
3.  **Python Dependencies**: This plugin requires the `Shapely` library. Install it in your UE Python environment:
    *   Navigate to: `C:\Program Files\Epic Games\UE_5.x\Engine\Binaries\ThirdParty\Python3\Win64`
    *   Run command: `python.exe -m pip install shapely`

## Quick Start
1.  **Open the Tool**: Locate the provided Editor Utility Widget (EUW) in your Content Browser, right-click, and select **Run Editor Utility Widget**.
2.  **Configure City Theme (Data Asset)**:
    *   Find the default Data Asset (e.g., `DA_DefaultTheme`) included in the package and double-click to open it.
    *   In the `Buildings` array, replace the default placeholder Static Meshes with your own building models.
    *   Customize the spawn weight and scale range for each building, then click Save.
3.  **Define Generation Boundary**:
    *   Click **Bound_Update** on the EUW panel to draw the generation bounding box.
    *   Click **Select Bound** to move or rotate the box within the viewport. Once adjusted, **you must click Bound_Update again** to refresh the underlying coordinate data.
4.  **Set Parameters & Generate**:
    *   Drag and drop your configured Data Asset into the `Theme Data` slot on the EUW panel.
    *   Adjust global parameters such as road width, density, and seed.
    *   Click **Generate** to instantly spawn your custom city!

## 鳴謝 (Credits & Acknowledgments)

本專案展示畫面中所使用的 3D 建築與物件模型，均來自知名免費開源資產庫 [Kenney](https://www.kenney.nl/)。
非常感謝創作者為開源社群提供如此高品質的資產。

*   **Asset Pack:** City Kit Suburban (2.0)
*   **Creator:** Kenney
*   **License:** Creative Commons Zero (CC0)
*   **Links:** [Website](https://www.kenney.nl/) | [Twitter](https://twitter.com/KenneyNL) | [Support/Donate](https://www.kenney.nl/donate)

---

The 3D building and object models used in the demonstration of this project are sourced from [Kenney](https://www.kenney.nl/). 
Huge thanks to the creator for providing such high-quality assets to the open-source community.

*   **Asset Pack:** City Kit Suburban (2.0)
*   **Creator:** Kenney
*   **License:** Creative Commons Zero (CC0)
*   **Links:** [Website](https://www.kenney.nl/) | [Twitter](https://twitter.com/KenneyNL) | [Support/Donate](https://www.kenney.nl/donate)
