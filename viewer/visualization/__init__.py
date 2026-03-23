"""可视化包 - CT + 剂量分布 + ROI轮廓四面板可视化"""

from .config import RenderConfig, CT_VMIN, CT_VMAX, DEFAULT_DOSE_THRESHOLD_RATIO
from .render import render_dose_overlay
from ._contours import draw_mask_contours
from ._colormap import build_dose_overlay_cmap

__all__ = [
    'RenderConfig',
    'render_dose_overlay',
    'draw_mask_contours',
    'build_dose_overlay_cmap',
    'CT_VMIN',
    'CT_VMAX',
    'DEFAULT_DOSE_THRESHOLD_RATIO',
]

__version__ = '1.0.0'
