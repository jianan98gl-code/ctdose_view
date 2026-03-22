"""ROI轮廓绘制"""
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Optional


def draw_mask_contours(ax, 
                       plane_masks: Dict[int, np.ndarray], 
                       roi_map: Dict[int, str],
                       colors: Dict[str, str], 
                       linewidths: Dict[str, float], 
                       show_legend: bool = False, 
                       origin_mode: str = 'upper', 
                       extent: Optional[list] = None):
    """在单个子图上绘制2D掩膜轮廓。
    
    Parameters:
        ax: matplotlib Axes对象
        plane_masks: ROI编号到2D掩膜的映射
        roi_map: ROI编号到名称的映射
        colors: ROI名称到颜色的映射
        linewidths: ROI名称到线宽的映射
        show_legend: 是否显示图例
        origin_mode: 图像原点位置 ('upper' 或 'lower')
        extent: 图像范围 [left, right, bottom, top]
    """
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
        ax.legend(handles, labels, loc='upper right', fontsize=9, framealpha=0.95, 
                  edgecolor='black', fancybox=True, shadow=True)
