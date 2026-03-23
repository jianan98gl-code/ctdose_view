"""CT + 剂量 + ROI 轮廓可视化主程序。"""

import os
import matplotlib.pyplot as plt
import nibabel as nib
from ReadNifti import ReadNifti
from cli_config import (
    build_cli_parser,
    get_param,
    load_config_file,
    parse_roi_ids,
    to_abs_path,
)
from data_paths import resolve_data_paths
from roi_config import build_roi_style_from_config
from utils import (
    resample,
    extract_slices,
    load_roi_reference_geometry,
    build_roi_masks,
    load_structures,
)
from visualization import RenderConfig, render_dose_overlay


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parser = build_cli_parser()
    args = parser.parse_args()
    config_path = args.config
    if config_path is None:
        default_config = os.path.join(base_dir, "config.yaml")
        if os.path.isfile(default_config):
            config_path = default_config
    cfg = load_config_file(config_path, base_dir)

    overrides = {
        "ct_nii_file": to_abs_path(get_param(args, cfg, "ct_nii", "ct_nii"), base_dir),
        "dose_nii_file": to_abs_path(get_param(args, cfg, "dose_nii", "dose_nii"), base_dir),
        "rs_dcm_file": to_abs_path(get_param(args, cfg, "rs_dcm", "rs_dcm"), base_dir),
        "ct_dicom_dir": to_abs_path(get_param(args, cfg, "ct_dicom_dir", "ct_dicom_dir"), base_dir),
        "rd_dcm_file": to_abs_path(get_param(args, cfg, "rd_dcm", "rd_dcm"), base_dir),
    }
    ct_nii_file, dose_nii_file, rs_dcm_file, ct_dicom_dir, rd_dcm_file = resolve_data_paths(base_dir, overrides)

    selected_roi_ids = parse_roi_ids(get_param(args, cfg, "roi_ids", "roi_ids", default=None))
    roi_map, roi_colors, roi_linewidths, unknown_ids = build_roi_style_from_config(cfg, selected_roi_ids)
    if unknown_ids:
        print(f"警告: 以下ROI编号未在默认ROI_MAP中定义，已忽略: {unknown_ids}")

    dose_threshold_ratio = float(get_param(args, cfg, "dose_threshold_ratio", "dose_threshold_ratio", default=0.1))
    scaling_policy = get_param(args, cfg, "scaling_policy", "scaling_policy", default="dicom_or_config")
    output_dpi = int(get_param(args, cfg, "dpi", "dpi", default=150))
    title = get_param(
        args,
        cfg,
        "title",
        "title",
        default="Head & Neck Cancer - Dose Distribution (CT+Dose)",
    )
    output_path = to_abs_path(
        get_param(args, cfg, "output", "output", default=os.path.join(os.path.dirname(base_dir), "ct_dose_roi_four_panel.png")),
        base_dir,
    )

    ct_img_nib = nib.load(ct_nii_file)
    dose_img_nib = nib.load(dose_nii_file)

    nifti_reader = ReadNifti()
    ct_array, ct_origin, ct_spacing, vmin, vmax = nifti_reader.load_ct_nifti(ct_nii_file)

    dose_grid_scaling = ReadNifti.load_dose_grid_scaling_from_rtdose(rd_dcm_file)
    config_scale = get_param(args, cfg, "dose_scale_factor", "dose_scale_factor", default=None)
    if config_scale is None:
        config_scale_env = os.environ.get("DOSE_SCALE_FACTOR")
        if config_scale_env:
            config_scale = float(config_scale_env)

    dose_array, dose_origin, dose_spacing = nifti_reader.load_dose_nifti(
        dose_nii_file,
        dose_grid_scaling=dose_grid_scaling,
        config_scale=config_scale,
        scaling_policy=scaling_policy,
    )

    _, _, _, dose_on_ct = resample(
        ct_array,
        ct_origin,
        ct_spacing,
        dose_array,
        dose_origin,
        dose_spacing,
        ct_affine=ct_img_nib.affine,
        dose_affine=dose_img_nib.affine,
    )
    
    z_idx = get_param(args, cfg, "z_idx", "z_idx", default=None)
    y_idx = get_param(args, cfg, "y_idx", "y_idx", default=None)
    x_idx = get_param(args, cfg, "x_idx", "x_idx", default=None)
    # 可以输 z_idx, y_idx, x_idx 到 extract_slices 来指定切片位置，默认会选取中心切片
    z_mid, y_mid, x_mid = extract_slices(ct_array, dose_on_ct, z_idx=z_idx, y_idx=y_idx, x_idx=x_idx)

    structures = load_structures(rs_dcm_file)
    rois = structures["rois"]

    roi_ct_origin, roi_ct_spacing, roi_ct_orientation = load_roi_reference_geometry(ct_dicom_dir)
    roi_masks = build_roi_masks(
        rois,
        ct_array.shape,
        roi_ct_origin,
        roi_ct_spacing,
        roi_ct_orientation,
        roi_map,
    )

    dose_max = float(dose_on_ct.max())

    print("重采样完成")
    print(f"  CT shape:              {ct_array.shape}")
    print(f"  Dose resampled shape:  {dose_on_ct.shape}")
    print(f"  Dose max:              {dose_max:.2f} Gy")
    scaling_info = nifti_reader.last_dose_scaling_info
    print("  Dose scaling:")
    print(f"    source:              {scaling_info.get('scale_source', 'none')}")
    print(f"    input unit:          {scaling_info.get('input_unit', 'raw_grid')}")
    print(f"    output unit:         {scaling_info.get('output_unit', 'Gy')}")
    print(f"    scale factor:        {scaling_info.get('scale_factor', 1.0):.8f}")
    print(f"    raw max:             {scaling_info.get('raw_max', 0.0):.4f}")
    print(f"    scaled max:          {scaling_info.get('scaled_max', 0.0):.4f}")
    print(f"  Available ROI masks:   {len(roi_masks)}")

    config = RenderConfig(roi_map=roi_map, colors=roi_colors, linewidths=roi_linewidths)
    fig = render_dose_overlay(
        ct_array=ct_array,
        dose_on_ct=dose_on_ct,
        roi_masks=roi_masks,
        config=config,
        ct_spacing=ct_spacing,
        z_idx=z_mid,
        y_idx=y_mid,
        x_idx=x_mid,
        vmin=vmin,
        vmax=vmax,
        dose_max=dose_max,
        dose_threshold_ratio=dose_threshold_ratio,
        title=title,
    )

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    fig.savefig(output_path, dpi=output_dpi, facecolor="white")
    print(f"已保存: {output_path}")
    if not args.no_show:
        plt.show()
        print("Done! Image displayed.")
    else:
        print("Done! Image saved without display.")


if __name__ == "__main__":
    main()