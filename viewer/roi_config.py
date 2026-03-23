"""ROI配置解析与构建工具。"""

from typing import Dict, List, Optional, Tuple

DEFAULT_COLOR = "white"
DEFAULT_LINEWIDTH = 1.5


def _normalize_roi_map(raw_map: Optional[Dict]) -> Optional[Dict[int, str]]:
    if raw_map is None:
        return None
    if not isinstance(raw_map, dict):
        raise ValueError("roi_map 必须是字典，键为ROI编号")
    norm_map: Dict[int, str] = {}
    for k, v in raw_map.items():
        norm_map[int(k)] = str(v)
    return norm_map


def _normalize_str_dict(raw_dict: Optional[Dict], key_name: str) -> Optional[Dict[str, str]]:
    if raw_dict is None:
        return None
    if not isinstance(raw_dict, dict):
        raise ValueError(f"{key_name} 必须是字典")
    return {str(k): str(v) for k, v in raw_dict.items()}


def _normalize_float_dict(raw_dict: Optional[Dict], key_name: str) -> Optional[Dict[str, float]]:
    if raw_dict is None:
        return None
    if not isinstance(raw_dict, dict):
        raise ValueError(f"{key_name} 必须是字典")
    return {str(k): float(v) for k, v in raw_dict.items()}


def build_roi_style(
    selected_roi_ids: Optional[List[int]],
    roi_map: Optional[Dict[int, str]] = None,
    roi_colors: Optional[Dict[str, str]] = None,
    roi_linewidths: Optional[Dict[str, float]] = None,
) -> Tuple[Dict[int, str], Dict[str, str], Dict[str, float], List[int]]:
    """构建ROI映射、颜色和线宽配置。"""
    if not roi_map:
        raise ValueError("缺少 roi_map，请在配置文件中提供 roi_map")

    base_map = roi_map
    base_colors = roi_colors or {}
    base_linewidths = roi_linewidths or {}

    if selected_roi_ids is None:
        active_map = dict(base_map)
        unknown_ids: List[int] = []
    else:
        active_map = {k: base_map[k] for k in selected_roi_ids if k in base_map}
        unknown_ids = [rid for rid in selected_roi_ids if rid not in base_map]

    if not active_map:
        raise ValueError("ROI选择为空，请检查 --roi-ids 或配置文件中的 roi_ids")

    active_colors = {name: base_colors.get(name, DEFAULT_COLOR) for name in active_map.values()}
    active_linewidths = {name: base_linewidths.get(name, DEFAULT_LINEWIDTH) for name in active_map.values()}

    return active_map, active_colors, active_linewidths, unknown_ids


def build_roi_style_from_config(cfg: Dict, selected_roi_ids: Optional[List[int]]) -> Tuple[Dict[int, str], Dict[str, str], Dict[str, float], List[int]]:
    """从配置字典中读取ROI风格（缺省时回落到默认配置）。"""
    cfg_roi_map = _normalize_roi_map(cfg.get("roi_map"))
    cfg_roi_colors = _normalize_str_dict(cfg.get("roi_colors"), "roi_colors")
    cfg_roi_linewidths = _normalize_float_dict(cfg.get("roi_linewidths"), "roi_linewidths")

    return build_roi_style(
        selected_roi_ids=selected_roi_ids,
        roi_map=cfg_roi_map,
        roi_colors=cfg_roi_colors,
        roi_linewidths=cfg_roi_linewidths,
    )
