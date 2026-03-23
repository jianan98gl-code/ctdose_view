"""CLI和配置文件解析工具。"""

import argparse
import importlib
import json
import os
from typing import Any, Dict, List, Optional


def to_abs_path(path: Optional[str], base_dir: str) -> Optional[str]:
    if not path:
        return None
    expanded = os.path.expanduser(path)
    if os.path.isabs(expanded):
        return os.path.normpath(expanded)
    return os.path.normpath(os.path.join(base_dir, expanded))


def load_config_file(config_path: Optional[str], base_dir: str) -> Dict[str, Any]:
    if not config_path:
        return {}

    abs_config = to_abs_path(config_path, base_dir)
    if not abs_config or not os.path.isfile(abs_config):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(abs_config, "r", encoding="utf-8") as f:
        if abs_config.lower().endswith((".yaml", ".yml")):
            try:
                yaml = importlib.import_module("yaml")
            except ImportError as exc:
                raise ImportError("读取YAML配置需要安装PyYAML: pip install pyyaml") from exc
            data = yaml.safe_load(f) or {}
        elif abs_config.lower().endswith(".json"):
            data = json.load(f)
        else:
            raise ValueError("仅支持 .yaml/.yml/.json 配置文件")

    if not isinstance(data, dict):
        raise ValueError("配置文件顶层必须是对象（键值对）")
    return data


def parse_roi_ids(raw_roi_ids) -> Optional[List[int]]:
    if raw_roi_ids is None:
        return None
    if isinstance(raw_roi_ids, list):
        return [int(v) for v in raw_roi_ids]
    if isinstance(raw_roi_ids, str):
        parts = [p.strip() for p in raw_roi_ids.split(",") if p.strip()]
        return [int(v) for v in parts]
    raise ValueError("roi_ids 需为逗号分隔字符串或整型列表")


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CT + Dose + ROI 四面板可视化")
    parser.add_argument("--config", type=str, default=None, help="配置文件路径(.yaml/.yml/.json)")

    parser.add_argument("--ct-nii", type=str, default=None, help="CT NIfTI 路径")
    parser.add_argument("--dose-nii", type=str, default=None, help="Dose NIfTI 路径")
    parser.add_argument("--rs-dcm", type=str, default=None, help="RTSTRUCT DICOM 路径")
    parser.add_argument("--ct-dicom-dir", type=str, default=None, help="CT DICOM 目录")
    parser.add_argument("--rd-dcm", type=str, default=None, help="RTDOSE DICOM 路径(可选)")

    parser.add_argument("--output", type=str, default=None, help="输出图片路径")
    parser.add_argument("--title", type=str, default=None, help="图像标题")
    parser.add_argument("--roi-ids", type=str, default=None, help="ROI编号列表，例如: 45,43,41")

    parser.add_argument("--z-idx", type=int, default=None, help="Axial切片索引")
    parser.add_argument("--y-idx", type=int, default=None, help="Coronal切片索引")
    parser.add_argument("--x-idx", type=int, default=None, help="Sagittal切片索引")

    parser.add_argument("--dose-threshold-ratio", type=float, default=None, help="剂量显示阈值比例")
    parser.add_argument(
        "--scaling-policy",
        type=str,
        choices=["dicom_or_config", "config_only", "none"],
        default=None,
        help="剂量缩放策略",
    )
    parser.add_argument("--dose-scale-factor", type=float, default=None, help="配置剂量缩放因子")
    parser.add_argument("--dpi", type=int, default=None, help="输出图片DPI")
    parser.add_argument("--no-show", action="store_true", help="保存后不弹出图窗")
    return parser


def get_param(cli_args, cfg: Dict[str, Any], cli_attr: str, cfg_key: str, default=None):
    value = getattr(cli_args, cli_attr)
    if value is not None:
        return value
    return cfg.get(cfg_key, default)
