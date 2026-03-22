import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.colors import LinearSegmentedColormap
from utils import _pad_center_2d

def draw_mask_contours(ax, 
                       plane_masks, 
                       roi_map, colors, 
                       linewidths, 
                       show_legend=False, 
                       origin_mode='upper', 
                       extent=None):
    
    """在单个子图上绘制2D掩膜轮廓。"""
    if not plane_masks:
        return

    added_to_legend = set()
    for roi_num in roi_map:
        if roi_num not in plane_masks:
            continue

        mask_2d = plane_masks[roi_num]
        if not np.any(mask_2d):
            continue

        name = roi_map[roi_num]
        color = colors[name]
        lw = linewidths[name]
        contour_kwargs = {
            'levels': [0.5],
            'colors': [color],
            'linewidths': lw,
            'origin': origin_mode,
        }
        if extent is not None:
            contour_kwargs['extent'] = extent
        ax.contour(mask_2d.astype(np.float32), **contour_kwargs)
        if show_legend and name not in added_to_legend:
            added_to_legend.add(name)

    if show_legend and added_to_legend:
        handles = [plt.Line2D([0], [0], color=colors[name], lw=2.0) for name in added_to_legend]
        labels = list(added_to_legend)
        ax.legend(handles, labels, loc='upper right', fontsize=9, framealpha=0.95, edgecolor='black', fancybox=True, shadow=True)


def _build_canvas_slice(ct_slice, dose_slice, plane_masks, canvas_h_mm, canvas_w_mm, row_mm, col_mm, vmin):
    """为单个切面构建 canvas，padding 到统一尺寸。"""
    target_h = int(np.round(canvas_h_mm / row_mm))
    target_w = int(np.round(canvas_w_mm / col_mm))

    ct_padded = _pad_center_2d(ct_slice, target_h, target_w, vmin)
    dose_padded = _pad_center_2d(dose_slice, target_h, target_w, 0.0)
    masks_padded = {
        roi_num: _pad_center_2d(mask_2d.astype(np.uint8), target_h, target_w, 0).astype(bool)
        for roi_num, mask_2d in plane_masks.items()
    }
    return ct_padded, dose_padded, masks_padded

def _prepare_plane_slices(ct_array, dose_on_ct, roi_masks, z_idx, y_idx, x_idx, vmin, vmax):
    """提取 4 个切面的 CT、剂量和 ROI 掩膜数据。"""
    axial_masks = {roi_num: mask[z_idx] for roi_num, mask in roi_masks.items()}
    coronal_masks = {roi_num: mask[:, y_idx, :] for roi_num, mask in roi_masks.items()}
    sagittal_masks = {roi_num: mask[:, :, x_idx] for roi_num, mask in roi_masks.items()}
    mip_masks = {roi_num: np.max(mask, axis=0) for roi_num, mask in roi_masks.items()}

    ct_mip = np.clip(np.max(ct_array, axis=0), vmin, vmax)
    dose_mip = np.max(dose_on_ct, axis=0)

    return {
        'axial': (np.clip(ct_array[z_idx], vmin, vmax), dose_on_ct[z_idx], axial_masks),
        'coronal': (np.clip(ct_array[:, y_idx, :], vmin, vmax), dose_on_ct[:, y_idx, :], coronal_masks),
        'sagittal': (np.clip(ct_array[:, :, x_idx], vmin, vmax), dose_on_ct[:, :, x_idx], sagittal_masks),
        'mip': (ct_mip, dose_mip, mip_masks),
    }

def _compute_canvas_geometry(ct_array, ct_spacing, z_idx, y_idx, x_idx):
    """计算 canvas 尺寸（mm）和纵横比。"""
    sz, sy, sx = ct_spacing
    
    axial_h_mm = ct_array[z_idx].shape[0] * sy
    axial_w_mm = ct_array[z_idx].shape[1] * sx
    coronal_h_mm = ct_array[:, y_idx, :].shape[0] * sz
    coronal_w_mm = ct_array[:, y_idx, :].shape[1] * sx
    sagittal_h_mm = ct_array[:, :, x_idx].shape[0] * sz
    sagittal_w_mm = ct_array[:, :, x_idx].shape[1] * sy
    
    ct_mip = np.max(ct_array, axis=0)
    mip_h_mm = ct_mip.shape[0] * sy
    mip_w_mm = ct_mip.shape[1] * sx

    canvas_w_mm = max(axial_w_mm, coronal_w_mm, sagittal_w_mm, mip_w_mm)
    canvas_h_mm = max(axial_h_mm, coronal_h_mm, sagittal_h_mm, mip_h_mm)
    canvas_box_aspect = canvas_h_mm / canvas_w_mm if canvas_w_mm else 1.0

    return canvas_w_mm, canvas_h_mm, canvas_box_aspect


def _create_figure_layout():
    """创建 figure 和 gridspec 布局。"""
    fig = plt.figure(figsize=(14.4, 11.4), dpi=110, facecolor='white')
    grid = fig.add_gridspec(
        nrows=2, ncols=3,
        width_ratios=[1.0, 1.0, 0.18],
        left=0.045, right=0.958, top=0.895, bottom=0.055,
        wspace=0.02, hspace=0.03,
    )
    axes = np.array([
        [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])],
        [fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])],
    ])
    side_grid = grid[:, 2].subgridspec(2, 1, height_ratios=[0.50, 0.50], hspace=0.03)
    cax = fig.add_subplot(side_grid[0, 0])
    legend_ax = fig.add_subplot(side_grid[1, 0])
    
    return fig, axes, cax, legend_ax


def _draw_single_panel(ax, ct_plot, dose_plot, masks_plot, panel_title, 
                       canvas_w_mm, canvas_h_mm, canvas_box_aspect, 
                       dose_masked, cmap, dose_threshold, dose_max, 
                       vmin, vmax, dose_interp, origin_mode, full_extent):
    """绘制单个面板（CT + 剂量叠加 + ROI 轮廓）。"""
    ax.set_box_aspect(canvas_box_aspect)
    ax.set_anchor('C')
    ax.set_facecolor('black')
    
    # 绘制 CT
    ax.imshow(ct_plot, cmap='gray', vmin=vmin, vmax=vmax, interpolation='none',
              aspect='equal', origin=origin_mode, extent=full_extent)
    
    # 绘制剂量叠加
    overlay_obj = ax.imshow(dose_masked, cmap=cmap, vmin=dose_threshold, vmax=dose_max,
                            interpolation=dose_interp, alpha=0.7, aspect='equal',
                            origin=origin_mode, extent=full_extent)
    
    # 绘制 ROI 轮廓
    draw_mask_contours(ax, masks_plot, show_legend=False, origin_mode=origin_mode, extent=full_extent)
    
    # 设置坐标轴
    ax.set_xlim(0, canvas_w_mm)
    ax.set_ylim(0, canvas_h_mm)
    ax.axis('off')
    
    # 添加标题标签
    ax.text(0.02, 0.98, panel_title, transform=ax.transAxes,
            ha='left', va='top', fontsize=10.5, fontweight='bold', color='white',
            bbox=dict(facecolor='black', alpha=0.42, edgecolor='none', pad=2.0))
    
    return overlay_obj


def _add_legend_to_axes(legend_ax, present_roi_names, colors):
    """在指定 axes 上添加 ROI 图例。"""
    legend_pos = legend_ax.get_position()
    legend_ax.set_position([
        legend_pos.x0 + legend_pos.width * 0.02,
        legend_pos.y0 - legend_pos.height * 0.03,
        legend_pos.width * 0.96,
        legend_pos.height * 1.08,
    ])
    legend_ax.axis('off')
    
    if present_roi_names:
        handles = [plt.Line2D([0], [0], color=colors[name], lw=2.2) for name in present_roi_names]
        legend = legend_ax.legend(
            handles, present_roi_names,
            loc='lower right', bbox_to_anchor=(0.98, 0.02), ncol=1, fontsize=9.0,
            frameon=False, prop={'family': 'Arial', 'size': 9.0},
            columnspacing=0.6, handlelength=2.4, borderpad=0.1, labelspacing=0.44,
        )
        legend.set_title("ROI", prop={'family': 'Arial', 'size': 10.2, 'weight': 'bold'})


def _add_colorbar_to_axes(fig, cax, overlay_obj, dose_max, dose_threshold):
    """在指定 axes 上添加色条。"""
    cax_pos = cax.get_position()
    cax.set_position([
        cax_pos.x0 + cax_pos.width * 0.18,
        cax_pos.y0 + cax_pos.height * 0.015,
        cax_pos.width * 0.24,
        cax_pos.height * 0.97,
    ])

    cbar = fig.colorbar(overlay_obj, cax=cax)
    cbar.set_label('Dose (Gy)', fontsize=12, fontweight='bold', fontname='Arial')

    # 计算色条刻度
    tick_candidates = np.arange(10, int(np.ceil(dose_max / 10.0)) * 10 + 1, 10, dtype=int)
    major_ticks = [int(t) for t in tick_candidates if dose_threshold <= t <= dose_max]
    if not major_ticks:
        major_ticks = [int(np.round(dose_threshold)), int(np.round(dose_max))]

    cbar.set_ticks(major_ticks)
    cbar.ax.set_yticklabels([str(t) for t in major_ticks], fontname='Arial', fontsize=9)
    cbar.ax.yaxis.set_minor_locator(MultipleLocator(5))
    cbar.ax.tick_params(which='major', length=5, width=1.0)
    cbar.ax.tick_params(which='minor', length=3, width=0.8)


def build_dose_overlay_cmap():
    # 色阶设计，高剂量红，低剂量蓝
    return LinearSegmentedColormap.from_list(
        "dose_overlay",
        [
            (0.0, 0.0, 1.0, 0.80), 
            (0.0, 1.0, 1.0, 0.75), 
            (0.0, 1.0, 0.0, 0.70),
            (1.0, 1.0, 0.0, 0.65), 
            (1.0, 0.5, 0.0, 0.60),
            (1.0, 0.0, 0.0, 0.55),
        ],
        N=256,
    )


def visualize_three_planes_overlay(
    ct_array,
    dose_on_ct,
    roi_masks,
    ct_spacing,
    z_idx,
    y_idx,
    x_idx,
    vmin,
    vmax,
    dose_max,
    roi_map,
    dose_threshold_ratio=0.1,
    title="Head & Neck Cancer - Dose Distribution (CT+Dose)"
):
    """
    终：可视化 CT、剂量分布和 ROI 轮廓的四面板视图。
    一些关键参数说明
        ct_array: CT 图像数据
        dose_on_ct: 重采样到 CT 空间的剂量数据
        roi_masks: ROI 掩膜字典
        ct_spacing: CT 间距 [z, y, x]
        z_idx, y_idx, x_idx: 切面索引
        dose_threshold_ratio: 剂量阈值比例
    """
    # 初始化参数
    dose_threshold = dose_max * dose_threshold_ratio
    cmap = build_dose_overlay_cmap()
    sz, sy, sx = ct_spacing
    
    # 获取存在的 ROI 名称
    present_roi_names = [
        roi_map[roi_num] for roi_num in roi_map
        if roi_num in roi_masks and np.any(roi_masks[roi_num])
    ]
    
    # 创建 figure 和布局
    fig, axes, cax, legend_ax = _create_figure_layout()
    
    # 计算几何参数
    canvas_w_mm, canvas_h_mm, canvas_box_aspect = _compute_canvas_geometry(
        ct_array, ct_spacing, z_idx, y_idx, x_idx
    )
    full_extent = [0, canvas_w_mm, 0, canvas_h_mm]
    
    # 准备切面数据
    plane_slices = _prepare_plane_slices(ct_array, dose_on_ct, roi_masks, z_idx, y_idx, x_idx, vmin, vmax)
    
    # 定义 4 个面板的绘制配置
    plane_config = [
        (axes[0, 0], 'axial', sy, sx, 'none', 'lower', f"Axial (Z={z_idx})"),
        (axes[0, 1], 'coronal', sz, sx, 'bilinear', 'lower', f"Coronal (Y={y_idx})"),
        (axes[1, 0], 'sagittal', sz, sy, 'bilinear', 'lower', f"Sagittal (X={x_idx})"),
        (axes[1, 1], 'mip', sy, sx, 'bilinear', 'lower', "Dose MIP (Axial Projection)"),
    ]
    
    overlay_obj = None
    for ax, plane_name, row_mm, col_mm, dose_interp, origin_mode, panel_title in plane_config:
        ct_slice, dose_slice, masks = plane_slices[plane_name]
        
        # 构建 canvas
        ct_plot, dose_plot, masks_plot = _build_canvas_slice(
            ct_slice, dose_slice, masks, canvas_h_mm, canvas_w_mm, row_mm, col_mm, vmin
        )
        
        # 准备剂量叠加
        dose_masked = np.ma.masked_less(dose_plot, dose_threshold)
        
        # 绘制面板
        overlay_obj = _draw_single_panel(
            ax, ct_plot, dose_plot, masks_plot, panel_title,
            canvas_w_mm, canvas_h_mm, canvas_box_aspect,
            dose_masked, cmap, dose_threshold, dose_max,
            vmin, vmax, dose_interp, origin_mode, full_extent
        )
    
    # 添加图例和色条
    _add_legend_to_axes(legend_ax, present_roi_names)
    _add_colorbar_to_axes(fig, cax, overlay_obj, dose_max, dose_threshold)
    
    # 设置标题
    fig.suptitle(title, fontsize=17, fontweight='bold', y=0.978)
    
    return fig