import unreal
import json
import os
import random
import math

def spawn_zoned_buildings(json_path, asset_folder_path, default_z_offset=0.0, enable_line_trace=False):
    # ==========================================
    # 1. 讀取 JSON 佈局數據
    # ==========================================
    if not os.path.exists(json_path):
        unreal.log_error(f"找不到 JSON: {json_path}")
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        layout_data = json.load(f)
    if not layout_data:
        return

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

    HIGH_THRESHOLD = 3000.0
    LOW_THRESHOLD  = 1000.0
    SCALE = 12.0

    high_rises, mid_rises, low_rises, all_meshes = [], [], [], []
    mesh_extents = {}

    for path in asset_paths:
        asset_data = unreal.EditorAssetLibrary.find_asset_data(path)
        if asset_data and asset_data.asset_class_path.asset_name == "StaticMesh":
            mesh = asset_data.get_asset()
            bounds = mesh.get_bounds()
            hx = bounds.box_extent.x * SCALE
            hy = bounds.box_extent.y * SCALE
            height = bounds.box_extent.z * 2.0

            mesh_extents[mesh] = (hx, hy)
            all_meshes.append(mesh)

            if height >= HIGH_THRESHOLD:   high_rises.append(mesh)
            elif height >= LOW_THRESHOLD:  mid_rises.append(mesh)
            else:                          low_rises.append(mesh)

    if not all_meshes:
        unreal.log_error("找不到任何靜態網格！")
        return

    with unreal.ScopedEditorTransaction("Spawn/Update City HISM"):
        # ==========================================
        # 4. 先行 Wipe！無差別清空橡皮擦邏輯 (確保移除舊有碰撞)[cite: 6]
        # ==========================================
        city_actor = None
        for actor in unreal.EditorLevelLibrary.get_all_level_actors():
            if actor.get_actor_label() == "CityManager_Actor":
                city_actor = actor
                break
                
        if not city_actor:
            city_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.Actor.static_class(), unreal.Vector(0,0,0), unreal.Rotator(0,0,0)
            )
            city_actor.set_actor_label("CityManager_Actor")

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

# ==========================================
if __name__ == "__main__":
    project_dir = unreal.Paths.project_saved_dir()
    spawn_zoned_buildings(
        json_path=os.path.join(project_dir, "building_layout_data.json"),
        asset_folder_path="/Game/City_Generate/CityMesh",
        default_z_offset=0.0,
        enable_line_trace=True  
    )