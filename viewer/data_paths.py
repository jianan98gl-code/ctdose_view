"""输入数据路径发现与校验工具。"""

import os
from typing import Dict, Optional, Tuple


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


def _find_first_rtdose_file(candidate_roots):
    for root in candidate_roots:
        npc_dir = os.path.join(root, "NPC_401")
        if not os.path.isdir(npc_dir):
            continue
        for name in os.listdir(npc_dir):
            if name.startswith("RD.") and name.endswith(".dcm"):
                return os.path.join(npc_dir, name)
    return None


def resolve_data_paths(base_dir: str, overrides: Optional[Dict[str, Optional[str]]] = None) -> Tuple[str, str, str, str, Optional[str]]:
    overrides = overrides or {}

    parent_dir = os.path.dirname(base_dir)
    workspace_dir = os.path.dirname(parent_dir)

    candidate_roots = []
    for root in [base_dir, parent_dir, os.path.join(workspace_dir, "ct_dose_view")]:
        norm = os.path.normpath(root)
        if norm not in candidate_roots and os.path.isdir(norm):
            candidate_roots.append(norm)

    ct_nii_file = overrides.get("ct_nii_file") or _find_first_existing_path(
        candidate_roots, ["Volume data", "201 Extended FOV iDose (3).nii"]
    )
    dose_nii_file = overrides.get("dose_nii_file") or _find_first_existing_path(
        candidate_roots, ["Volume data", "205 Eclipse Doses.nii"]
    )
    rs_dcm_file = overrides.get("rs_dcm_file") or _find_first_existing_path(
        candidate_roots, ["NPC_401", "RS.NPC_401.AutoPlan.dcm"]
    )
    ct_dicom_dir = overrides.get("ct_dicom_dir") or _find_first_ct_folder(candidate_roots)
    rd_dcm_file = overrides.get("rd_dcm_file") or _find_first_rtdose_file(candidate_roots)

    if ct_nii_file and not os.path.isfile(ct_nii_file):
        raise FileNotFoundError(f"CT NIfTI 不存在: {ct_nii_file}")
    if dose_nii_file and not os.path.isfile(dose_nii_file):
        raise FileNotFoundError(f"Dose NIfTI 不存在: {dose_nii_file}")
    if rs_dcm_file and not os.path.isfile(rs_dcm_file):
        raise FileNotFoundError(f"RTSTRUCT 不存在: {rs_dcm_file}")
    if ct_dicom_dir and not os.path.isdir(ct_dicom_dir):
        raise FileNotFoundError(f"CT DICOM 目录不存在: {ct_dicom_dir}")
    if rd_dcm_file and not os.path.isfile(rd_dcm_file):
        raise FileNotFoundError(f"RTDOSE 不存在: {rd_dcm_file}")

    if not (ct_nii_file and dose_nii_file and rs_dcm_file and ct_dicom_dir):
        raise FileNotFoundError(
            "未找到完整输入数据。请确认存在: "
            "Volume data/201 Extended FOV iDose (3).nii, "
            "Volume data/205 Eclipse Doses.nii, "
            "NPC_401/RS.NPC_401.AutoPlan.dcm 以及 NPC_401 下 CT.*.dcm。"
        )

    return ct_nii_file, dose_nii_file, rs_dcm_file, ct_dicom_dir, rd_dcm_file
