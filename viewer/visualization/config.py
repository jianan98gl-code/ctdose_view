"""可视化配置"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class RenderConfig:
    """渲染配置参数"""
    roi_map: Dict[int, str]  # ROI编号到名称的映射
    colors: Dict[str, str]   # ROI名称到颜色的映射
    linewidths: Dict[str, float]  # ROI名称到线宽的映射


# 图表尺寸配置
FIGURE_WIDTH = 14.4
FIGURE_HEIGHT = 11.4
FIGURE_DPI = 110

# CT显示范围（HU）
CT_VMIN = -150
CT_VMAX = 350

# 剂量显示配置
DEFAULT_DOSE_THRESHOLD_RATIO = 0.1
DOSE_COLORMAP_LEVELS = 6
