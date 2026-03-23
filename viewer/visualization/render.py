"""主渲染函数"""
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Optional

from .config import RenderConfig
from ._colormap import build_dose_overlay_cmap
from ._contours import draw_mask_contours
from .layout import create_figure_layout, add_legend_to_axes, add_colorbar_to_axes
from .canvas import compute_canvas_geometry, prepare_plane_slices, build_canvas_slice


def render_dose_overlay(ct_array: np.ndarray,
                       dose_on_ct: np.ndarray,
                       roi_masks: Dict[int, np.ndarray],
                       config: RenderConfig,
                       ct_spacing: np.ndarray,
                       z_idx: int,
                       y_idx: int,
                       x_idx: int,
                       vmin: float,
                       vmax: float,
                       dose_max: float,
                       dose_threshold_ratio: float = 0.1,
                       title: str = "Head & Neck Cancer - Dose Distribution (CT+Dose)") -> plt.Figure:
    """可视化CT、剂量分布和ROI轮廓的四面板视图。
    
    Parameters:
        ct_array: CT图像数据
        dose_on_ct: 重采样到CT空间的剂量数据
        roi_masks: ROI掩膜字典 {roi_num: 3D_mask_array}
        config: RenderConfig对象，包含roi_map、colors、linewidths
        ct_spacing: CT间距 [z, y, x]
        z_idx, y_idx, x_idx: 切面索引
        vmin, vmax: CT显示范围
        dose_max: 剂量最大值
        dose_threshold_ratio: 剂量阈值比例（默认0.1）
        title: 图表标题
    
    Returns:
        matplotlib Figure对象
    """
    # 初始化参数
    dose_threshold = dose_max * dose_threshold_ratio
    cmap = build_dose_overlay_cmap()
    sz, sy, sx = ct_spacing
    
    # 获取存在的ROI名称
    present_roi_names = [
        config.roi_map[roi_num] for roi_num in config.roi_map
        if roi_num in roi_masks and np.any(roi_masks[roi_num])
    ]
    
    # 创建figure和布局
    fig, axes, cax, legend_ax = create_figure_layout()
    
    # 计算几何参数
    canvas_w_mm, canvas_h_mm, canvas_box_aspect = compute_canvas_geometry(
        ct_array, ct_spacing, z_idx, y_idx, x_idx
    )
    full_extent = [0, canvas_w_mm, 0, canvas_h_mm]
    
    # 准备切面数据
    plane_slices = prepare_plane_slices(
        ct_array, dose_on_ct, roi_masks, z_idx, y_idx, x_idx, vmin, vmax
    )
    
    # 定义4个面板的绘制配置
    plane_config = [
        (axes[0, 0], 'axial', sy, sx, 'none', 'lower', f"Axial (Z={z_idx})"),
        (axes[0, 1], 'coronal', sz, sx, 'bilinear', 'lower', f"Coronal (Y={y_idx})"),
        (axes[1, 0], 'sagittal', sz, sy, 'bilinear', 'lower', f"Sagittal (X={x_idx})"),
        (axes[1, 1], 'mip', sy, sx, 'bilinear', 'lower', "Dose MIP (Axial Projection)"),
    ]
    
    overlay_obj = None
    for ax, plane_name, row_mm, col_mm, dose_interp, origin_mode, panel_title in plane_config:
        ct_slice, dose_slice, masks = plane_slices[plane_name]
        
        # 构建canvas
        ct_plot, dose_plot, masks_plot = build_canvas_slice(
            ct_slice, dose_slice, masks, canvas_h_mm, canvas_w_mm, row_mm, col_mm, vmin
        )
        
        # 准备剂量叠加（掩膜低于阈值的部分）
        dose_masked = np.ma.masked_less(dose_plot, dose_threshold)
        
        # 绘制单个面板
        overlay_obj = _draw_single_panel(
            ax, ct_plot, dose_plot, masks_plot, panel_title,
            canvas_w_mm, canvas_h_mm, canvas_box_aspect,
            dose_masked, cmap, dose_threshold, dose_max,
            vmin, vmax, dose_interp, origin_mode, full_extent,
            config
        )
    
    # 添加图例和色条
    add_legend_to_axes(legend_ax, present_roi_names, config.colors)
    add_colorbar_to_axes(fig, cax, overlay_obj, dose_max, dose_threshold)
    
    # 设置标题
    fig.suptitle(title, fontsize=17, fontweight='bold', y=0.978)
    
    return fig


def _draw_single_panel(ax: plt.Axes,
                      ct_plot: np.ndarray,
                      dose_plot: np.ndarray,
                      masks_plot: Dict[int, np.ndarray],
                      panel_title: str,
                      canvas_w_mm: float,
                      canvas_h_mm: float,
                      canvas_box_aspect: float,
                      dose_masked: np.ma.MaskedArray,
                      cmap,
                      dose_threshold: float,
                      dose_max: float,
                      vmin: float,
                      vmax: float,
                      dose_interp: str,
                      origin_mode: str,
                      full_extent: list,
                      config: RenderConfig) -> object:
    """绘制单个面板（CT + 剂量叠加 + ROI轮廓）。
    
    Parameters:
        ax: matplotlib Axes对象
        ct_plot, dose_plot: 切面数据
        masks_plot: ROI掩膜
        panel_title: 面板标题
        canvas_*: Canvas参数
        dose_masked: 掩膜的剂量数据
        cmap: Colormap
        dose_threshold, dose_max: 剂量参数
        vmin, vmax: CT显示范围
        dose_interp: 插值方法
        origin_mode: 原点位置
        full_extent: 图像范围
        config: RenderConfig对象
    
    Returns:
        imshow返回的Image对象（用于colorbar）
    """
    ax.set_box_aspect(canvas_box_aspect)
    ax.set_anchor('C')
    ax.set_facecolor('black')
    
    # 绘制CT
    ax.imshow(ct_plot, cmap='gray', vmin=vmin, vmax=vmax, interpolation='none',
              aspect='equal', origin=origin_mode, extent=full_extent)
    
    # 绘制剂量叠加
    overlay_obj = ax.imshow(dose_masked, cmap=cmap, vmin=dose_threshold, vmax=dose_max,
                            interpolation=dose_interp, alpha=0.7, aspect='equal',
                            origin=origin_mode, extent=full_extent)
    
    # 绘制ROI轮廓
    draw_mask_contours(ax, masks_plot, config.roi_map, config.colors, config.linewidths,
                      show_legend=False, origin_mode=origin_mode, extent=full_extent)
    
    # 设置坐标轴
    ax.set_xlim(0, canvas_w_mm)
    ax.set_ylim(0, canvas_h_mm)
    ax.axis('off')
    
    # 添加标题标签
    ax.text(0.02, 0.98, panel_title, transform=ax.transAxes,
            ha='left', va='top', fontsize=10.5, fontweight='bold', color='white',
            bbox=dict(facecolor='black', alpha=0.42, edgecolor='none', pad=2.0))
    
    return overlay_obj
