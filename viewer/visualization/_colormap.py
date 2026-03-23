"""剂量叠加Colormap构建"""
from matplotlib.colors import LinearSegmentedColormap
from .config import DOSE_COLORMAP_LEVELS


def build_dose_overlay_cmap():
    """创建剂量叠加色图，高剂量红，低剂量蓝。
    
    Returns:
        LinearSegmentedColormap: 从蓝色（低剂量）到红色（高剂量）的colormap
    """
    return LinearSegmentedColormap.from_list(
        "dose_overlay",
        [
            (0.0, 0.0, 1.0, 0.80),   # 蓝
            (0.0, 1.0, 1.0, 0.75),   # 青
            (0.0, 1.0, 0.0, 0.70),   # 绿
            (1.0, 1.0, 0.0, 0.65),   # 黄
            (1.0, 0.5, 0.0, 0.60),   # 橙
            (1.0, 0.0, 0.0, 0.55),   # 红
        ],
        N=256,
    )
