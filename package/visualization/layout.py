"""图表布局管理"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from typing import Tuple, List


def create_figure_layout() -> Tuple[plt.Figure, np.ndarray, plt.Axes, plt.Axes]:
    """创建figure和gridspec布局。
    
    Returns:
        Tuple[Figure, axes_array, colorbar_ax, legend_ax]:
            - fig: matplotlib Figure对象
            - axes: 2x2 Axes数组（四个主绘制面板）
            - cax: 色条Axes
            - legend_ax: 图例Axes
    """
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


def add_legend_to_axes(legend_ax: plt.Axes, 
                      present_roi_names: List[str],
                      colors: dict) -> None:
    """在指定axes上添加ROI图例。
    
    Parameters:
        legend_ax: matplotlib Axes对象
        present_roi_names: 存在的ROI名称列表
        colors: ROI名称到颜色的映射
    """
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


def add_colorbar_to_axes(fig: plt.Figure,
                        cax: plt.Axes,
                        overlay_obj,
                        dose_max: float,
                        dose_threshold: float) -> None:
    """在指定axes上添加色条。
    
    Parameters:
        fig: matplotlib Figure对象
        cax: colorbar Axes
        overlay_obj: imshow返回的Image对象
        dose_max: 剂量最大值
        dose_threshold: 剂量阈值
    """
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
