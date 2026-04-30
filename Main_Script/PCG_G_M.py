import unreal
import random
import math
from collections import namedtuple

from shapely.geometry import Point, LineString, Polygon

from shapely.ops import unary_union, polygonize
from shapely.geometry import LineString, MultiLineString

Point2D = namedtuple('Point2D', ['x', 'y'])
Point3D = namedtuple('Point3D', ['x', 'y', 'z'])
T_Range = namedtuple('T_Range', ['min', 'max'])

def input_content_here(a=None,b=None,c=None,d=None):
    unreal.log(f"Input checked:\n {a},\n {b}, \n{c}, \n{d}")


def populate_2d(width, length, count, seed=123):
    """
    使用純 Python random 實現的自然分布採樣
    """
    if count <= 0:
        return []
    
    random.seed(seed)
    points = []
    
    # 1. 計算網格分佈 (避免 ZeroDivisionError)
    # 即使 count=1，grid_res 都會係 1
    grid_res = int(math.sqrt(count))
    if grid_res < 1: 
        grid_res = 1

    # 直接用 grid_res 分段，唔好用 grid_res - 1
    w_step = width / grid_res
    l_step = length / grid_res

    # 起始點 (左下角)
    start_x = -width / 2
    start_y = -length / 2

    # 2. 遍歷網格並加入隨機抖動
    for i in range(grid_res):
        for j in range(grid_res):
            if len(points) >= count:
                break
                
            # 每個點都被限制喺自己嘅小格子內，但喺格子入面係隨機嘅
            # 咁樣可以保證唔會成堆點擠埋一齊（解決“過於集中”）
            # 亦都唔會排成直線（解決“過於整齊”）
            
            # 加入 0.1 到 0.9 嘅抖動，保留邊界感防止重疊
            off_x = random.uniform(0.1, 0.9) * w_step
            off_y = random.uniform(0.1, 0.9) * l_step
            
            px = start_x + (i * w_step) + off_x
            py = start_y + (j * l_step) + off_y
            
            points.append(Point2D(px,py))

    # 3. 補漏：如果因為開方取整導致點數唔夠，隨機喺全場補齊
    while len(points) < count:
        px = random.uniform(-width/2, width/2)
        py = random.uniform(-length/2, length/2)
        points.append(Point2D(px,py))

    return points

def visualize_points(points_input,locatin_point_list):
    """
    上层封装函数：处理 2D/3D 数据转换及坐标系对齐
    :param points: 你的计算结果列表，支持 [(x,y), ...] 或 [(x,y,z), ...]
    :param target_actor: 如果传入 Actor，则将点视为该 Actor 的局部坐标并转为世界坐标
    :param z_offset: 额外给点一个高度，防止点埋在地面（Landscape）下面看不见
    """
    unreal_points = []

    for pt in points_input:

        if len(pt) == 2:
            # 输入是 (x, y)，补全为 (x, y, z_offset)
            vec = unreal.Vector(pt[0], pt[1],0)
            unreal_points.append(vec)
            #unreal.log(f"Converted 2D point {pt} to 3D Unreal Vector {vec}")
        elif len(pt) >= 3:
            # 输入已经是 (x, y, z)
            vec = unreal.Vector(pt[0], pt[1], pt[2] + 0)
            unreal_points.append(vec)
        else:
            unreal.log_warning(f"Invalid point format: {pt}, skipping.")
            continue

    unreal_points = local_to_world(locatin_point_list,unreal_points)

    # 4. 调用底层渲染函数
    visualize_points_UE(unreal_points)


def visualize_points_UE(points):
    """
    底层渲染函数：负责在 UE 编辑器中画点
    """
    # 注意：在较新版本的 UE Python 中，使用 unreal.EditorLevelLibrary.get_editor_world()
    # 如果是在 Actor 内部运行，也可以用 actor.get_world()
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    if not world:
        unreal.log_error("找不到 World 上下文，无法绘制 Debug 点。")
        return

    # 使用 SystemLibrary 绘制
    # 参数说明：World, Position, Size, Color, Duration
    for pt in points:
        unreal.SystemLibrary.draw_debug_point(
            world,
            pt,
            size=50.0, 
            point_color=unreal.LinearColor(1.0, 0.2, 0.2, 1.0), # 浅红色
            duration=10.0
        )
    
    unreal.log(f"Successfully visualized {len(points)} points.")

def Scale(point_list, scale_factor,center_point):
    scaled_points = []
    for p in point_list:
        # 以中心点为基准进行缩放
        scaled_x = center_point.x + (p.x - center_point.x) * scale_factor
        scaled_y = center_point.y + (p.y - center_point.y) * scale_factor
        scaled_z = p.z  # Z轴保持不变
        scaled_points.append((scaled_x, scaled_y, scaled_z))

# def local_to_world(point_list, point_to_changed):
#     actor_location = unreal.MathLibrary.get_vector_array_average(point_list)
#     #unreal.log(f"actor location {actor_location}")
#     world_points = []
#     for pt  in point_to_changed:
#         world_x = pt.x + actor_location.x
#         world_y = pt.y + actor_location.y
#         world_z = pt.z + actor_location.z
#         world_points.append(unreal.Vector(world_x, world_y, world_z))
    
#     #unreal.log(f"Converted {len(point_to_changed)} local points to world points based on actor location {actor_location}.")
    
#     return world_points

def local_to_world(point_list, point_to_changed):
    # ✅ 同样改为纯 Python 计算，不依赖 get_vector_array_average
    if not point_list:
        return point_to_changed
    
    avg_x = sum(float(p.x) for p in point_list) / len(point_list)
    avg_y = sum(float(p.y) for p in point_list) / len(point_list)
    avg_z = sum(float(p.z) for p in point_list) / len(point_list)

    world_points = []
    for pt in point_to_changed:
        world_points.append(unreal.Vector(
            pt.x + avg_x,
            pt.y + avg_y,
            pt.z + avg_z
        ))
    return world_points

def uv_point_sample(w,l, u_v_sample_count):# calculate the local sample point position
    sample_point = []
    w_step = w / u_v_sample_count
    l_step = l / u_v_sample_count
    for i in range(u_v_sample_count):
        sample_x = -w/2 + w_step * i
        for j in range(u_v_sample_count):
            sample_y = -l/2 + l_step * j
            sample_point.append(Point2D(sample_x, sample_y))
    unreal.log(f"uv sample point count: {len(sample_point)}")
    return sample_point

def safe_unit_2d(v):
    # 解构元组 (a, b)
    a, b = v
    
    # 计算 2D 向量长度
    length = math.sqrt(a**2 + b**2)
    
    # 防止除以零
    if length == 0:
        return (0.0, 0.0)
    
    # 直接计算并返回 2D 元组
    return (a / length, b / length)

def cross_product_2d(v1, v2):
    # v1 = (x1, y1), v2 = (x2, y2)
    # 返回的是 Z 轴方向的数值大小
    return v1[0] * v2[1] - v1[1] * v2[0]

def dot_product_2d(v1, v2):
    # v1 = (x1, y1), v2 = (x2, y2)
    return v1[0] * v2[0] + v1[1] * v2[1]

def rotate_90(v):
    # v = (x, y)
    return (-v[1], v[0])

def length_2d(v):
    return math.sqrt(v[0]**2 + v[1]**2)


def build_spatial_grid(joint_points, grid_size):
    """
    接收来自 populate_2d 的 unreal.Vector 列表
    """
    grid = {}
    for j in joint_points:
        # 使用 .x .y 访问 unreal.Vector 更加直观
        ix = int(j.x // grid_size)
        iy = int(j.y // grid_size)
        cell_key = (ix, iy)
        
        if cell_key not in grid:
            grid[cell_key] = []
        grid[cell_key].append(j)
        
    unreal.log(f"Spatial grid built with {len(grid)} active cells.")
    return grid

def flow_field(uv_sample_points, joint_points, A, B, influence_rad=400.0):
    """
    第二阶段：计算流场 (全局双重循环，与 Rhino 逻辑一致)
    """
    major_list = []
    minor_list = []
    
    inf_rad_sq = influence_rad * influence_rad
    strength = 5.0
    
    for px, py in uv_sample_points:
        # 1. 计算全局背景流 (Base Flow)
        # 对应 Rhino: V_final = rg.Vector3d(1, 1, 0) * 0.5
        fx = 1
        fy = 1
        
        # 2. 局部干扰点进行“路径偏转” (Slingshot / Deflection)
        for j in joint_points:
            # 兼容读取 (处理 joint_points 可能是 unreal.Vector 或 Point2D)
            jx = j.x if hasattr(j, 'x') else j[0]
            jy = j.y if hasattr(j, 'y') else j[1]
            
            # 计算点到干扰点的位移
            dx = jx - px
            dy = jy - py
            
            dist_sq = dx*dx + dy*dy
            
            if dist_sq < inf_rad_sq:
                dist = math.sqrt(dist_sq) + 1e-6
                
                # 计算干扰权重
                weight = (1.0 - dist / influence_rad) ** 2
                
                # 归一化 dir_to_c
                dir_c_x = dx / dist
                dir_c_y = dy / dist
                
                # 找到当前背景流的法线，并判断在左侧还是右侧
                # 计算叉积 Z 分量: V_final.X * dir_to_c.Y - V_final.Y * dir_to_c.X
                cross_z = fx * dir_c_y - fy * dir_c_x
                
                # 计算侧向向量 (逆时针旋转90度: -y, x)
                side_x = -fy
                side_y = fx
                
                # 如果干扰点在流向的左侧 (cross.Z > 0)，向右偏转
                if cross_z > 0:
                    side_x = -side_x
                    side_y = -side_y
                
                # 混合偏转
                # deflection = (A * dir_to_c + B * side_vec) * weight * Strength
                deflect_mult = weight * strength
                deflect_x = (A * dir_c_x + B * side_x) * deflect_mult
                deflect_y = (A * dir_c_y + B * side_y) * deflect_mult
                
                # 累加到当前前进向量
                fx += deflect_x
                fy += deflect_y
                
        # 3. 规范化最终结果
        m_len_sq = fx*fx + fy*fy
        if m_len_sq > 1e-12:
            m_len = math.sqrt(m_len_sq)
            fx /= m_len
            fy /= m_len
        else:
            fx, fy = 1.0, 0.0 # 退化保护
            
        major_list.append((fx, fy))
        # minor 等于 major 旋转 90 度
        minor_list.append((-fy, fx))
        
    return major_list, minor_list


def potential_seed_point(w, l, seed_count):
    min_w, max_w = -w/2, w/2
    min_l, max_l = -l/2, l/2

    seed_points = []
    # 确保每条边至少有一个点 (注意加上 int() 防止之前出现过的 float 报错)
    count_per_edge = int(max(1, seed_count // 4))

    # 定义四条边的参数：(起始坐标, 结束坐标, 固定坐标轴, 是否是横向边)
    edges = [
        (min_w, max_w, max_l, True),  # Top: y = max_l, x varies
        (min_w, max_w, min_l, True),  # Bottom: y = min_l, x varies
        (min_l, max_l, min_w, False), # Left: x = min_w, y varies
        (max_l, min_l, max_w, False)  # Right: x = max_w, y varies
    ]

    for start, end, fixed, is_horizontal in edges:
        edge_length = end - start
        
        # 整体两端的安全缓冲距离 (5%)
        padding = edge_length * 0.05
        safe_start = start + padding
        safe_end = end - padding

        # 计算出安全区域的总长度，并将其均分为 count_per_edge 个「段落/小格子」
        safe_length = safe_end - safe_start
        step = safe_length / count_per_edge

        for i in range(count_per_edge):
            # 获取当前这个「小格子」的起点和终点
            cell_start = safe_start + (i * step)
            cell_end = cell_start + step
            
            # 为了防止左边格子的点随机到了最右侧，右边格子的点随机到了最左侧导致贴在一起
            # 我们给每个小格子内部也加上一点点缓冲 (例如格长的 15%)
            cell_padding = step * 0.15
            
            # 核心：只在当前这个格子的范围内进行随机
            pos = random.uniform(cell_start + cell_padding, cell_end - cell_padding)
            
            if is_horizontal:
                # 横向边：pos 是 x，fixed 是 y
                pt = unreal.Vector(pos, fixed, 0.0)
            else:
                # 纵向边：fixed 是 x，pos 是 y
                pt = unreal.Vector(fixed, pos, 0.0)
                
            seed_points.append(pt)

    return seed_points


# draw road by field
def sample_field_optimized(p, pts, vecs, k=3):
    """
    2D 向量場採樣 (IDW 演算法)
    :param p: 採樣點 (unreal.Vector 或 [x,y])
    :param pts: 原始採樣網格點列表 (uv_sample_point)
    :param vecs: 對應網格點的向量列表 (major_list)
    :param k: 考慮最近的 k 個點
    """
    px, py = p.x, p.y
    candidates = []

    # 1. 計算所有點的距離
    for i in range(len(pts)):
        ref_pt = pts[i]
        # 使用平方距離 (Distance Squared)，省去 math.sqrt
        dx = px - ref_pt.x
        dy = py - ref_pt.y
        dist_sq = dx*dx + dy*dy
        
        # 極小距離處理 (直接返回)
        if dist_sq < 1e-8:
            return vecs[i]
        
        candidates.append((dist_sq, i))

    # 2. 排序取前 k 個 (針對小範圍 k，sort 的效率足夠)
    candidates.sort(key=lambda x: x[0])
    top_k = candidates[:k]

    # 3. 加權求和
    sum_vx = 0.0
    sum_vy = 0.0
    total_weight = 0.0

    for d_sq, idx in top_k:
        # IDW 公式：權重 = 1 / d^2
        # 因為我們已經有 d_sq，直接用即可，效率更高
        weight = 1.0 / d_sq
        
        v = vecs[idx]
        vx, vy = v
        sum_vx += vx * weight
        sum_vy += vy * weight
        total_weight += weight

    # 4. 歸一化與結果輸出
    if total_weight > 0:
        # 計算平均向量
        vx = sum_vx / total_weight
        vy = sum_vy / total_weight
        
        # 2D 歸一化 (Unitize)
        v_len = math.sqrt(vx*vx + vy*vy)
        if v_len > 1e-6:
            return unreal.Vector(vx / v_len, vy / v_len, 0.0)
            
    return unreal.Vector(0, 0, 0)

from shapely.geometry import Point, LineString
import math

# --- 辅助函数：安全获取 x, y 坐标 ---
def get_xy(pt):
    """兼容 unreal.Vector 和 Python tuple/list 的读取"""
    if hasattr(pt, 'x'):
        return pt.x, pt.y
    return pt[0], pt[1]

# --- 1. 向量采样 ---
def sample_field_shapely(p_coords, pts_coords, vecs, k=3):
    # 安全读取采样点坐标
    px, py = get_xy(p_coords)
    
    candidates = []
    for i, ref_pt in enumerate(pts_coords):
        rx, ry = get_xy(ref_pt)
        dx, dy = px - rx, py - ry
        dist_sq = dx*dx + dy*dy
        
        if dist_sq < 1e-7: 
            return get_xy(vecs[i]) # 如果重合，直接返回该向量的 (x,y)
            
        candidates.append((dist_sq, vecs[i]))
    
    candidates.sort(key=lambda x: x[0])
    top_k = candidates[:k]
    
    sum_vx, sum_vy, total_w = 0.0, 0.0, 0.0
    for d_sq, v in top_k:
        vx, vy = get_xy(v)
        weight = 1.0 / d_sq
        sum_vx += vx * weight
        sum_vy += vy * weight
        total_w += weight
    
    if total_w > 0:
        vx = sum_vx / total_w
        vy = sum_vy / total_w
        mag = math.sqrt(vx*vx + vy*vy)
        if mag > 1e-6:
            return (vx/mag, vy/mag) # 返回纯 Python Tuple (x, y)
    return (0, 0)

# --- 2. 主生成函数 ---
def generate_roads_shapely(seeds, grid_pts, vecs, boundary_poly=None, step=100.0, max_steps=50, snap_dist=50.0):
    roads = [] # 储存 Shapely LineString 对象
    
    for seed in seeds:
        # 获取纯元组格式 (x, y)
        sx, sy = get_xy(seed)
        pts_chain = [(sx, sy)]
        current = (sx, sy)
        
        for _ in range(max_steps):
            # 1. 采样方向
            v = sample_field_shapely(current, grid_pts, vecs)
            if v == (0, 0): break
            
            # 2. 前进 (使用纯数学计算)
            next_px = current[0] + v[0] * step
            next_py = current[1] + v[1] * step
            next_p = (next_px, next_py)
            next_p_obj = Point(next_p)
            
            # 3. 边界检测 (如果传入了 boundary_poly)
            if boundary_poly is not None:
                if not boundary_poly.contains(next_p_obj):
                    # 如果出界了，可以选择用之前的 clamp 逻辑，或者直接打断
                    break
            
            # 4. 吸附已有路
            is_snap = False
            for road in roads:
                # distance 是计算点到线的最短距离
                if road.distance(next_p_obj) < snap_dist:
                    is_snap = True
                    break
            
            # 5. 记录并前行
            pts_chain.append(next_p)
            current = next_p
            
            if is_snap: 
                break
            
        # 至少 2 个点才能构成线段
        if len(pts_chain) >= 2:
            roads.append(LineString(pts_chain))
            
    return roads

# geometry operation
def partition_parcels(boundary_poly, road_list_1, road_list_2):
    """
    將兩組路徑整合並分割邊界範圍
    :param boundary_poly: 你的原始範圍 (Shapely Polygon)
    :param road_list_1: Major roads
    :param road_list_2: Minor roads
    :return: List of Polygons (Parcels)
    """
    # 1. 將所有 LineString 擺入同一個 list
    all_lines = road_list_1 + road_list_2
    
    # 2. 加入邊界線 (呢步好緊要！否則邊緣嘅地塊封唔埋口)
    # 提取 Boundary 嘅外環線
    all_lines.append(boundary_poly.exterior)
    
    # 3. Unary Union：將所有相交嘅線段喺交點處「打斷」
    # 呢個動作會將「兩條交叉線」變成「四條喺中心點連接嘅線」
    merged_network = unary_union(all_lines)
    
    # 4. Polygonize：搵出所有封閉嘅區域
    # 呢個 Function 會返翻一個 iterator，入面全部系 Polygon
    parcels = list(polygonize(merged_network))
    
    # 5. 過濾：只保留喺 Boundary 入面嘅地塊 (防止浮點運算產生嘅外部碎片)
    final_parcels = [p for p in parcels if boundary_poly.contains(p.representative_point())]
    
    return final_parcels

def process_parcels_attributes(parcels, offset_dist=-800.0):
    parcel_data = []
    parcel_id_counter = 0  # 用獨立嘅 ID 計數器，因為一個舊地塊可能會分裂成兩個新地塊
    
    for p in parcels:
        # 向內縮進
        inner_poly = p.buffer(offset_dist, join_style=2)
        
        if inner_poly.is_empty:
            continue
            
        # 1. 檢查幾何類型，處理分裂嘅情況
        polys_to_process = []
        if inner_poly.geom_type == 'MultiPolygon':
            # 如果分裂咗，提取所有內部嘅獨立多邊形
            polys_to_process = list(inner_poly.geoms)
        elif inner_poly.geom_type == 'Polygon':
            # 如果冇分裂，直接放入列表
            polys_to_process = [inner_poly]
        else:
            continue # 忽略其他奇怪嘅幾何形狀 (例如縮到變成一條 LineString)
            
        # 2. 遍歷處理每一個有效嘅多邊形
        for single_poly in polys_to_process:
            # 加入微小面積過濾，防止浮點數誤差產生嘅 0.0001 面積碎片導致後續出錯
            if single_poly.area < 10.0:
                continue
                
            # 提取數據
            parcel_info = {
                "id": parcel_id_counter,
                "area": single_poly.area,
                "centroid": (single_poly.centroid.x, single_poly.centroid.y),
                "coords": list(single_poly.exterior.coords), # 依家絕對安全，因為肯定係 Polygon
                # 根據面積決定層數：面積越大，層數越多
                "layers": 1 if single_poly.area < 5000 else (3 if single_poly.area < 15000 else 5)
            }
            parcel_data.append(parcel_info)
            parcel_id_counter += 1  # ID 遞增
            
    return parcel_data
# 1. 修正採樣函數：確保回傳字典格式並修正機率邏輯
def sample_points_with_edge_bias(parcels_data, density_factor=0.00001, falloff=10000.0):
    culled_points = []

    for p_data in parcels_data:
        poly = Polygon(p_data['coords'])
        if not poly.is_valid:
            continue
            
        min_x, min_y, max_x, max_y = poly.bounds
        area = poly.area
        
        # --- 動態點數計算邏輯 (分層閾值) ---
        if area < 1000:
            sample_count = 0  # 面積太小，直接不生成 (例如路口安全島)
            
        elif area < 5000:
            sample_count = random.randint(1, 3)  # 小地塊：保證至少有 1~3 個點
            
        elif area < 20000:
            # 中等地塊：使用較高的密度
            sample_count = int(area * 0.001) 
            
        else:
            # 超大地塊：使用極低密度，並且加上硬上限保護 UE
            sample_count = int(area * 0.0001)
        # ------------------------------------

        for _ in range(sample_count):
            random_pt = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))

            if poly.contains(random_pt):
                dist_to_edge = poly.exterior.distance(random_pt)
                # 指數衰減：離邊緣越遠機率越低
                prob_keep = math.exp(-dist_to_edge / falloff)
                
                if random.random() < prob_keep:
                    culled_points.append({
                        "pos": (random_pt.x, random_pt.y),
                        "parcel_id": p_data['id']
                    })
                    
    return culled_points

def snap_and_get_tangent(culled_points, parcels_data):
    """
    将采样点吸附至地块边界，并计算该处的切线方向
    """
    # 建立 ID 索引方便快速查询地块
    parcel_lookup = {p['id']: Polygon(p['coords']) for p in parcels_data}
    
    refined_results = []
    delta = 0.1 # 用于计算切线的微小偏移量

    for pt_data in culled_points:
        pid = pt_data['parcel_id']
        poly = parcel_lookup.get(pid)
        if not poly: continue
        
        # 1. 取得地块的外环线 (Exterior)
        boundary = poly.exterior
        current_pt = Point(pt_data['pos'])
        
        # 2. 线性参考：点在边界线上的投影距离
        dist_on_line = boundary.project(current_pt)
        
        # 3. 吸附：根据距离获取边界上的精准坐标 (Pull Back)
        snapped_pt = boundary.interpolate(dist_on_line)
        
        # 4. 计算切线 (Tangent)
        # 在投影点前后各取一小段距离的点，连成向量
        p1 = boundary.interpolate(max(0, dist_on_line - delta))
        p2 = boundary.interpolate(min(boundary.length, dist_on_line + delta))
        
        # 切线向量
        tx = p2.x - p1.x
        ty = p2.y - p1.y
        mag = math.sqrt(tx*tx + ty*ty)
        
        if mag > 1e-6:
            tx /= mag
            ty /= mag
        else:
            tx, ty = 1.0, 0.0 # 退化情况默认方向
            
        # 5. 计算偏航角 (Yaw/Rotation) 
        # UE 中通常以 X 轴为正方向，atan2 返回弧度
        angle_rad = math.atan2(ty, tx)
        angle_deg = math.degrees(angle_rad)

        refined_results.append({
            "original_pos": pt_data['pos'],              # <--- 新增：保留原始在格地內部的座標
            "snapped_pos": (snapped_pt.x, snapped_pt.y), # 原本的吸附邊界座標
            "tangent": (tx, ty),
            "rotation_yaw": angle_deg,
            "parcel_id": pid
        })
        
    return refined_results

def visualize_roads(roads_list, location_point_list, color=unreal.LinearColor(0, 1, 0, 1)):
    """
    上層封裝函式：處理道路線段的座標轉換與渲染
    :param roads_list: 包含 Shapely LineString 物件的列表 (例如 road_1, road_2)
    :param location_point_list: 基準點列表，用於計算世界座標偏移
    :param color: 線條顏色，預設為綠色
    """
    world_road_segments = []
    
    for road in roads_list:
        # 從 LineString 提取點座標
        coords = list(road.coords)
        # 轉換為 unreal.Vector 格式
        local_vectors = [unreal.Vector(p[0], p[1], 10.0) for p in coords] # 稍微抬高防止穿模
        
        # 轉換為世界空間
        world_vectors = local_to_world(location_point_list, local_vectors)
        world_road_segments.append(world_vectors)

    # 執行底層繪製
    visualize_roads_UE(world_road_segments, color)

def visualize_roads_UE(road_chains, color):
    """
    底層渲染函式：在編輯器中使用 Draw Debug Line 繪製道路
    """
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        return

    for chain in road_chains:
        # 遍歷線段點位，兩兩連線
        for i in range(len(chain) - 1):
            p1 = chain[i]
            p2 = chain[i+1]
            unreal.SystemLibrary.draw_debug_line(
                world,
                p1,
                p2,
                line_color=color,
                duration=10.0,
                thickness=100.0
            )

    unreal.log(f"Successfully visualized {len(road_chains)} road chains.")


def spawn_zoned_buildings(json_data, asset_folder_path, 
                          default_z_offset=0.0, 
                          enable_line_trace=False,
                          label = "Building_Instance",
                          Mesh_Scale = 1.0):
    safe_label = str(label)
    # ==========================================
    # 1. 讀取 JSON 佈局數據
    # ==========================================

    layout_data = json_data

    world = unreal.EditorLevelLibrary.get_editor_world()

    # ==========================================
    # 2. 劃定「絕對清空大框」(Eraser Bounding Box)[cite: 6]
    # ==========================================
    all_x = [d["original_pos"][0] for d in layout_data]
    all_y = [d["original_pos"][1] for d in layout_data]
    
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    max_radius = math.sqrt(((max_x-min_x)/2)**2 + ((max_y-min_y)/2)**2)

    padding = 2000.0
    clear_min_x = min_x - padding
    clear_max_x = max_x + padding
    clear_min_y = min_y - padding
    clear_max_y = max_y + padding

    # ==========================================
    # 3. 加載資產 & 預計算包圍盒大小
    # ==========================================
    asset_paths = unreal.EditorAssetLibrary.list_assets(asset_folder_path, recursive=False)

    # HIGH_THRESHOLD = 3000.0
    # LOW_THRESHOLD  = 1000.0
    SCALE = Mesh_Scale

    high_rises, mid_rises, low_rises, all_meshes = [], [], [], []
    mesh_extents = {}
    
    # 用嚟暫存第一波採集到嘅數據
    temp_mesh_data = [] 
    all_heights = []

    # ==========================================
    # 步驟 1：採集所有 Mesh 嘅高度與範圍數據
    # ==========================================
    for path in asset_paths:
        asset_data = unreal.EditorAssetLibrary.find_asset_data(path)
        if asset_data and asset_data.asset_class_path.asset_name == "StaticMesh":
            mesh = asset_data.get_asset()
            bounds = mesh.get_bounds()
            hx = bounds.box_extent.x * SCALE
            hy = bounds.box_extent.y * SCALE
            
            # 溫馨提示：如果你生成 Actor 嗰陣 Z 軸都會乘 SCALE，呢度建議改成 * 2.0 * SCALE
            height = bounds.box_extent.z * 2.0 

            mesh_extents[mesh] = (hx, hy)
            all_meshes.append(mesh)
            
            temp_mesh_data.append((mesh, height))
            all_heights.append(height)

    if not temp_mesh_data:
        unreal.log_error("找不到任何靜態網格！There is no static mesh found in the folder !")
        return

    # ==========================================
    # 步驟 2：根據分佈動態計算 Threshold
    # ==========================================
    max_h = max(all_heights)
    min_h = min(all_heights)
    height_diff = max_h - min_h

    # 將總高度差分為 3 等份 (可以按你需要調整比例，例如 0.6 同 0.3)
    HIGH_THRESHOLD = min_h + (height_diff * 0.66)
    LOW_THRESHOLD  = min_h + (height_diff * 0.33)

    unreal.log(f"動態高度劃分 -> 最矮 lowest: {min_h:.1f}, 最高 highest: {max_h:.1f}")
    unreal.log(f"分界線 -> 高樓 High threshold>= {HIGH_THRESHOLD:.1f}, 矮樓 Low threshold< {LOW_THRESHOLD:.1f}")

    # ==========================================
    # 步驟 3：正式分類
    # ==========================================
    for mesh, height in temp_mesh_data:
        if height >= HIGH_THRESHOLD:
            high_rises.append(mesh)
        elif height >= LOW_THRESHOLD:
            mid_rises.append(mesh)
        else:
            low_rises.append(mesh)
            
    unreal.log(f"分類結果 -> 高樓 high: {len(high_rises)}個, 中樓 Medium: {len(mid_rises)}個, 矮樓 low: {len(low_rises)}個")

    with unreal.ScopedEditorTransaction("Spawn/Update City HISM"):
        # ==========================================
        # 4. 先行 Wipe！無差別清空橡皮擦邏輯 (確保移除舊有碰撞)[cite: 6]
        # ==========================================
        city_actor = None
        for actor in unreal.EditorLevelLibrary.get_all_level_actors():
            if actor.get_actor_label() == safe_label:
                city_actor = actor
                break
                
        if not city_actor:
            # 將 Vector(0,0,0) 改為 Vector(center_x, center_y, 0.0)
            city_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.Actor.static_class(), unreal.Vector(center_x, center_y, 0.0), unreal.Rotator(0,0,0)
            )
            city_actor.set_actor_label(safe_label)

        hism_comps = {}
        for comp in city_actor.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent.static_class()):
            mesh = comp.get_editor_property("static_mesh")
            if mesh:
                hism_comps[mesh] = comp

        surviving_transforms = {} 
        for mesh, comp in hism_comps.items():
            surviving_transforms[mesh] = []
            instance_count = comp.get_instance_count()
            
            for i in range(instance_count):
                trans = comp.get_instance_transform(i, world_space=True)
                pos = trans.translation
                
                # 只要舊 Instance 落入清空框，無差別強拆！[cite: 6]
                if (clear_min_x <= pos.x <= clear_max_x) and (clear_min_y <= pos.y <= clear_max_y):
                    pass # 刪除
                else:
                    surviving_transforms[mesh].append(trans) # 保留

        # 瞬間清空場景中嘅所有舊 Instance！呢一步會同步清空舊建築嘅物理碰撞
        for comp in hism_comps.values():
            comp.clear_instances()


        # ==========================================
        # 5. 處理新數據 (射線測高 & 自我剔除)
        # ==========================================
        GRID_CELL = 5000.0  
        spatial_grid = {}   

        def grid_cells_for_box(bmin_x, bmax_x, bmin_y, bmax_y):
            ix0 = int(math.floor(bmin_x / GRID_CELL))
            ix1 = int(math.floor(bmax_x / GRID_CELL))
            iy0 = int(math.floor(bmin_y / GRID_CELL))
            iy1 = int(math.floor(bmax_y / GRID_CELL))
            return [(ix, iy) for ix in range(ix0, ix1+1) for iy in range(iy0, iy1+1)]

        def is_overlapping(bmin_x, bmax_x, bmin_y, bmax_y):
            for cell in grid_cells_for_box(bmin_x, bmax_x, bmin_y, bmax_y):
                for (ox1, ox2, oy1, oy2) in spatial_grid.get(cell, []):
                    if bmin_x < ox2 and bmax_x > ox1 and bmin_y < oy2 and bmax_y > oy1:
                        return True
            return False

        def register_box(bmin_x, bmax_x, bmin_y, bmax_y):
            box = (bmin_x, bmax_x, bmin_y, bmax_y)
            for cell in grid_cells_for_box(bmin_x, bmax_x, bmin_y, bmax_y):
                spatial_grid.setdefault(cell, []).append(box)

        new_buildings_data = [] 
        skipped_count = 0

        for data in layout_data:
            pos_x = data["original_pos"][0]
            pos_y = data["original_pos"][1]
            yaw   = data.get("rotation_yaw", 0.0)

            # 因為舊樓已經被 clear_instances() 清除，依家嘅 Line Trace 絕對安全，直達地面！
            if enable_line_trace:
                hit = unreal.SystemLibrary.line_trace_single(
                    world_context_object=world,
                    start=unreal.Vector(pos_x, pos_y, 100000.0),
                    end=unreal.Vector(pos_x, pos_y, -100000.0),
                    trace_channel=unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                    trace_complex=False,
                    actors_to_ignore=[],
                    draw_debug_type=unreal.DrawDebugTrace.NONE,
                    ignore_self=True
                )
                final_z = hit.to_tuple()[4].z if hit is not None else default_z_offset
            else:
                final_z = default_z_offset

            dx = pos_x - center_x
            dy = pos_y - center_y
            t = max(0.0, min(math.sqrt(dx*dx + dy*dy) / max_radius, 1.0))
            prob_high = (1.0 - t) ** 2
            prob_low  = t ** 2
            prob_mid  = max(0.0, 1.0 - prob_high - prob_low)

            valid_pools, valid_weights = [], []
            for pool, w in [(high_rises, prob_high), (mid_rises, prob_mid), (low_rises, prob_low)]:
                if pool:
                    valid_pools.append(pool)
                    valid_weights.append(w)

            selected_mesh = random.choice(
                random.choices(valid_pools, weights=valid_weights, k=1)[0]
                if valid_pools else all_meshes
            )

            ue_transform = unreal.Transform(
                location=unreal.Vector(pos_x, pos_y, final_z),
                rotation=unreal.Rotator(0.0, 0.0, yaw),              
                scale=unreal.Vector(SCALE, SCALE, SCALE)
            )

            hx, hy = mesh_extents[selected_mesh]
            buffer = 10.0
            bmin_x = pos_x - hx + buffer
            bmax_x = pos_x + hx - buffer
            bmin_y = pos_y - hy + buffer
            bmax_y = pos_y + hy - buffer

            if is_overlapping(bmin_x, bmax_x, bmin_y, bmax_y):
                skipped_count += 1
                continue  
                
            register_box(bmin_x, bmax_x, bmin_y, bmax_y)

            new_buildings_data.append({
                'mesh': selected_mesh,
                'transform': ue_transform
            })
            
        unreal.log(f"✅ 新數據處理完畢：準備生成 {len(new_buildings_data)} 棟，自我剔除跳過 {skipped_count} 個重疊點。")


        # ==========================================
        # 6. UE5 批量重新繪製 Subobject 流程 (Redraw)
        # ==========================================
        final_transforms_to_add = surviving_transforms 
        for new_b in new_buildings_data:
            mesh = new_b['mesh']
            if mesh not in final_transforms_to_add:
                final_transforms_to_add[mesh] = []
            final_transforms_to_add[mesh].append(new_b['transform'])

        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        
        for mesh, transforms in final_transforms_to_add.items():
            if mesh not in hism_comps:
                root_handles = subsystem.k2_gather_subobject_data_for_instance(city_actor)
                root_handle = root_handles[0]

                params = unreal.AddNewSubobjectParams(
                    parent_handle=root_handle,
                    new_class=unreal.HierarchicalInstancedStaticMeshComponent.static_class()
                )

                add_result = subsystem.add_new_subobject(params)
                sub_handle = add_result[0] if isinstance(add_result, tuple) else add_result

                find_result = subsystem.k2_find_subobject_data_from_handle(sub_handle)
                sub_data = find_result[1] if isinstance(find_result, tuple) else find_result
                
                new_comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(sub_data)
                new_comp.set_editor_property("static_mesh", mesh)
                hism_comps[mesh] = new_comp
                
            if transforms:
                hism_comps[mesh].add_instances(transforms, False, True)
                
        unreal.log(f"✅ 生成/更新完成！已無差別清空大框範圍，並寫入了 {len(new_buildings_data)} 棟新數據。")
        return len(new_buildings_data)


def main( Width, Length,point_list,road_width,seed,label,Mesh_Scale):
    unreal.log("entering main function")
    unreal.log(f"point_list: {point_list}, Width: {Width}, Length: {Length}")
    unreal.log(f"label in as : {label}")
    w = Width
    l = Length

    # configuration of some base data
    Area = w * l
    Area_per_House = 7000 * 12000
    possible_count = int(Area / Area_per_House)
    center_local = [0,0,0]

    #city arrangement config
    seed = seed
    core_count = Area // (Area_per_House * 100)
    sub_core_count = Area // (Area_per_House* 5)
    if core_count < 1:
        core_count = 1


    # sampling config
    min_dist = 10000
    U_V_Sample_count = 100

    # A,B config for flow field
    A = 0.01
    B = 0.3
    # 先計算網格的平均步長
    grid_step = ((Width + Length) / 2) / U_V_Sample_count
    # 強制影響半徑至少為網格步長的 2.5 到 3 倍
    influent_rad = grid_step * 15

    # 如果想保留原本手動控制的邏輯，可以使用 max() 保底：
    # influent_rad = max(((Width + Length)//2)//50, grid_step * 3.0)

    # joint point of city
    joint_point = []
    core_point = populate_2d(w*0.5, l*0.5, core_count, seed)
    joint_point_Add = populate_2d(w*0.8, l*0.8, sub_core_count)

    unreal.log(f"core_count: {core_count}; sub_core_coutn: {sub_core_count}")
    
    joint_point.extend(core_point)
    joint_point.extend(joint_point_Add)

    #uv sample point
    uv_sample_point = uv_point_sample(w,l,U_V_Sample_count)

    # flow field
    major_list, minor_list = flow_field(uv_sample_point, joint_point,A,B,influence_rad=influent_rad)

    edge_total_length = (Width + Length)*2
    total_edge_point_need = int(edge_total_length // (12000*2))

    seed_points = potential_seed_point(Width,Length,total_edge_point_need)

    road_1 = generate_roads_shapely(seed_points, uv_sample_point,major_list,step = 1000, max_steps= 300, snap_dist= 500)
    road_2 = generate_roads_shapely(seed_points, uv_sample_point,minor_list,step = 1000, max_steps= 300, snap_dist= 500)

    bound = Polygon([(-Width/2,-Length/2),(Width/2, - Length/2),(Width/2, Length/2),(-Width/2,Length/2)])

    parcle = partition_parcels(bound,road_1,road_2)
    parcle = process_parcels_attributes(parcle,offset_dist=-road_width)

    position_points = sample_points_with_edge_bias(parcle,density_factor=0.05,falloff=Width*0.3)
    direction_vec = snap_and_get_tangent(position_points,parcle)


   # --- 安全防護 1：防止點位過多卡死 UE ---
    point_count = len(direction_vec)
    unreal.log(f"準備處理與導出 {point_count} 個建築點位...")

    min_x = min(p.x for p in point_list)
    max_x = max(p.x for p in point_list)
    min_y = min(p.y for p in point_list)
    max_y = max(p.y for p in point_list)

    offset_x = (min_x + max_x) * 0.5
    offset_y = (min_y + max_y) * 0.5

    for item in direction_vec:
        orig_x, orig_y = item["original_pos"]
        snap_x, snap_y = item["snapped_pos"]
        
        item["original_pos"] = (float(orig_x) + offset_x, float(orig_y) + offset_y)
        item["snapped_pos"]   = (float(snap_x) + offset_x, float(snap_y) + offset_y)

    label = str(label)
    spawn_zoned_buildings(
        json_data=direction_vec,
        asset_folder_path="/Game/City_Generate/CityMesh",
        default_z_offset=0.0,
        enable_line_trace=True  ,
        label = label,
        Mesh_Scale=Mesh_Scale,
    )
    ...