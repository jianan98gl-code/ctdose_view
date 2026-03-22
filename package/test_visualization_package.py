"""测试新的visualization包结构"""
import sys
sys.path.insert(0, r'd:\python文件\view_ctdose\package')

# 测试导入
print("=" * 50)
print("测试导入...")
print("=" * 50)

try:
    from visualization import (
        RenderConfig,
        render_dose_overlay,
        draw_mask_contours,
        build_dose_overlay_cmap,
        CT_VMIN,
        CT_VMAX,
    )
    print("✓ 主包导入成功")
except Exception as e:
    print(f"✗ 主包导入失败: {e}")
    sys.exit(1)

# 测试子模块导入
try:
    from visualization.config import RenderConfig as RC
    from visualization.canvas import compute_canvas_geometry
    from visualization.layout import create_figure_layout
    from visualization._colormap import build_dose_overlay_cmap as cmap_builder
    print("✓ 子模块导入成功")
except Exception as e:
    print(f"✗ 子模块导入失败: {e}")
    sys.exit(1)

# 测试RenderConfig
print("\n" + "=" * 50)
print("测试RenderConfig...")
print("=" * 50)

roi_map = {1: 'Tumor', 2: 'Heart'}
colors = {'Tumor': 'red', 'Heart': 'blue'}
linewidths = {'Tumor': 2.0, 'Heart': 1.5}

config = RenderConfig(roi_map=roi_map, colors=colors, linewidths=linewidths)
print(f"✓ RenderConfig创建成功")
print(f"  - roi_map: {config.roi_map}")
print(f"  - colors: {config.colors}")
print(f"  - linewidths: {config.linewidths}")

# 测试colormap构建
print("\n" + "=" * 50)
print("测试Colormap构建...")
print("=" * 50)

try:
    cmap = build_dose_overlay_cmap()
    print(f"✓ Colormap构建成功: {cmap.name}")
except Exception as e:
    print(f"✗ Colormap构建失败: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("✓ 所有测试通过！")
print("=" * 50)
print("\n使用示例:")
print("""
config = RenderConfig(
    roi_map={1: 'Tumor', 2: 'Heart'},
    colors={'Tumor': 'red', 'Heart': 'blue'},
    linewidths={'Tumor': 2.0, 'Heart': 1.5}
)

fig = render_dose_overlay(
    ct_array=ct_data,
    dose_on_ct=dose_data,
    roi_masks=roi_masks_dict,
    config=config,
    ct_spacing=spacing_array,
    z_idx=50, y_idx=100, x_idx=80,
    vmin=-150, vmax=350, dose_max=50.0
)
""")
