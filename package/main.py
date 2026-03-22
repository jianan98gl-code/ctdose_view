"""CT + 剂量 + ROI 轮廓可视化主程序。"""

import os
import matplotlib.pyplot as plt
import nibabel as nib

from ReadNifti import ReadNifti
from utils import (
    resample,
    extract_slices,
    load_roi_reference_geometry,
    build_roi_masks,
    load_structures,
)
from visualization import RenderConfig, render_dose_overlay

# 可以手动调整需要显示的ROI编号和对应名称
ROI_MAP = {
    45: "GTV70-4",
    43: "GTVln66",
    41: "CTV60",
    40: "PTV6000",
    35: "BrainStem",
    13: "SpinalCord",
    20: "OpticChiasm",
    19: "OpticNrv_L",
    18: "OpticNrv_R",
    17: "Parotid_L",
    16: "Parotid_R",
}

ROI_COLORS = {
    "GTV70-4": "red",
    "GTVln66": "magenta",
    "CTV60": "limegreen",
    "PTV6000": "cyan",
    "BrainStem": "yellow",
    "SpinalCord": "turquoise",
    "OpticChiasm": "orange",
    "OpticNrv_L": "blue",
    "OpticNrv_R": "deepskyblue",
    "Parotid_L": "purple",
    "Parotid_R": "brown",
}

ROI_LINEWIDTHS = {
    "GTV70-4": 2.8,
    "GTVln66": 2.5,
    "CTV60": 1.8,
    "PTV6000": 1.5,
    "BrainStem": 1.8,
    "SpinalCord": 1.8,
    "OpticChiasm": 1.5,
    "OpticNrv_L": 1.5,
    "OpticNrv_R": 1.5,
    "Parotid_L": 1.8,
    "Parotid_R": 1.8,
}


def _find_first_existing_path(candidate_roots, rel_parts):
    for root in candidate_roots:
        path = os.path.join(root, *rel_parts)
        if os.path.exists(path):
            return path
    return None


def _find_first_ct_folder(candidate_roots):
    for root in candidate_roots:
        npc_dir = os.path.join(root, "NPC_401")
        if not os.path.isdir(npc_dir):
            continue
        for name in os.listdir(npc_dir):
            if name.startswith("CT.") and name.endswith(".dcm"):
                return npc_dir
    return None


def _resolve_data_paths(base_dir):
    parent_dir = os.path.dirname(base_dir)
    workspace_dir = os.path.dirname(parent_dir)

    candidate_roots = []
    for root in [base_dir, parent_dir, os.path.join(workspace_dir, "ct_dose_view")]:
        norm = os.path.normpath(root)
        if norm not in candidate_roots and os.path.isdir(norm):
            candidate_roots.append(norm)

    ct_nii_file = _find_first_existing_path(candidate_roots, ["Volume data", "201 Extended FOV iDose (3).nii"])
    dose_nii_file = _find_first_existing_path(candidate_roots, ["Volume data", "205 Eclipse Doses.nii"])
    rs_dcm_file = _find_first_existing_path(candidate_roots, ["NPC_401", "RS.NPC_401.AutoPlan.dcm"])
    ct_dicom_dir = _find_first_ct_folder(candidate_roots)

    if not (ct_nii_file and dose_nii_file and rs_dcm_file and ct_dicom_dir):
        raise FileNotFoundError(
            "未找到完整输入数据。请确认存在: "
            "Volume data/201 Extended FOV iDose (3).nii, "
            "Volume data/205 Eclipse Doses.nii, "
            "NPC_401/RS.NPC_401.AutoPlan.dcm 以及 NPC_401 下 CT.*.dcm。"
        )

    return ct_nii_file, dose_nii_file, rs_dcm_file, ct_dicom_dir


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ct_nii_file, dose_nii_file, rs_dcm_file, ct_dicom_dir = _resolve_data_paths(base_dir)

    ct_img_nib = nib.load(ct_nii_file)
    dose_img_nib = nib.load(dose_nii_file)

    nifti_reader = ReadNifti()
    ct_array, ct_origin, ct_spacing, vmin, vmax = nifti_reader.load_ct_nifti(ct_nii_file)
    dose_array, dose_origin, dose_spacing = nifti_reader.load_dose_nifti(dose_nii_file)

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
    
    #可以输z_idx, y_idx, x_idx 到 extract_slices 来指定切片位置，默认会选取中心切片
    z_mid, y_mid, x_mid = extract_slices(ct_array, dose_on_ct)

    structures = load_structures(rs_dcm_file)
    rois = structures["rois"]

    roi_ct_origin, roi_ct_spacing, roi_ct_orientation = load_roi_reference_geometry(ct_dicom_dir)
    roi_masks = build_roi_masks(
        rois,
        ct_array.shape,
        roi_ct_origin,
        roi_ct_spacing,
        roi_ct_orientation,
        ROI_MAP,
    )

    dose_max = float(dose_on_ct.max())

    print("重采样完成")
    print(f"  CT shape:              {ct_array.shape}")
    print(f"  Dose resampled shape:  {dose_on_ct.shape}")
    print(f"  Dose max:              {dose_max:.2f} Gy")
    print(f"  Available ROI masks:   {len(roi_masks)}")

    config = RenderConfig(roi_map=ROI_MAP, colors=ROI_COLORS, linewidths=ROI_LINEWIDTHS)
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
        dose_threshold_ratio=0.1,
        title="Head & Neck Cancer - Dose Distribution (CT+Dose)",
    )

    output_dir = os.path.dirname(base_dir)
    output_file = os.path.join(output_dir, "ct_dose_roi_four_panel.png")
    fig.savefig(output_file, dpi=150, facecolor="white")
    print(f"已保存: {output_file}")
    plt.show()
    print("Done! Image displayed.")


if __name__ == "__main__":
    main()