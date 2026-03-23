'''
读取NIfTI文件的工具类，提供了两个静态方法：
1. load_ct_nifti(ct_nii_file): 读取CT NIfTI文件
2. load_dose_nifti(dose_nii_file): 读取剂量 NIfTI文件
每个方法都返回图像数据数组、原点坐标、像素间距
'''

import numpy as np
import nibabel as nib
import pydicom
from typing import Optional, Dict

class ReadNifti:
    def __init__(self):
        self.last_dose_scaling_info: Dict[str, float] = {}

    @staticmethod
    def load_dose_grid_scaling_from_rtdose(rtdose_file: Optional[str]) -> Optional[float]:
        """从RTDOSE读取DoseGridScaling（若可用）。"""
        if not rtdose_file:
            return None

        ds = pydicom.dcmread(rtdose_file, stop_before_pixels=True)
        if hasattr(ds, "DoseGridScaling"):
            return float(ds.DoseGridScaling)
        return None

    @staticmethod
    def _extract_affine_info(affine):
        spacing = np.sqrt(np.sum(affine[:3, :3] ** 2, axis=0))
        origin = affine[:3, 3]
        return origin, spacing

    def load_ct_nifti(self, ct_nii_file: str):
        img = nib.load(ct_nii_file)
        ct_array = img.get_fdata().astype(np.float32)
        origin, spacing = self._extract_affine_info(img.affine)
    
        # 数据转为(Z,Y,X)；origin保持(X,Y,Z)，spacing返回为[Z,Y,X]以兼容下游轮廓函数
        ct_array = np.transpose(ct_array, (2, 1, 0))
        origin_xyz = np.array([origin[0], origin[1], origin[2]])
        spacing_zyx = np.array([spacing[2], spacing[1], spacing[0]])
    
        vmin, vmax = -150, 350
        return ct_array, origin_xyz, spacing_zyx, vmin, vmax

    def load_dose_nifti(
        self,
        dose_nii_file: str,
        dose_grid_scaling: Optional[float] = None,
        config_scale: Optional[float] = None,
        scaling_policy: str = "dicom_or_config",
    ):
        img = nib.load(dose_nii_file)
        dose_array = img.get_fdata().astype(np.float32)
        origin, spacing = self._extract_affine_info(img.affine)

        raw_max = float(dose_array.max())

        if scaling_policy not in {"dicom_or_config", "config_only", "none"}:
            raise ValueError(
                f"不支持的scaling_policy={scaling_policy}，可选: dicom_or_config/config_only/none"
            )

        scale_factor = 1.0
        scale_source = "none"
        if scaling_policy == "dicom_or_config":
            if dose_grid_scaling is not None:
                scale_factor = float(dose_grid_scaling)
                scale_source = "dicom_dose_grid_scaling"
            elif config_scale is not None:
                scale_factor = float(config_scale)
                scale_source = "config_scale"
        elif scaling_policy == "config_only" and config_scale is not None:
            scale_factor = float(config_scale)
            scale_source = "config_scale"

        dose_array = dose_array * scale_factor
        scaled_max = float(dose_array.max())

        self.last_dose_scaling_info = {
            "raw_max": raw_max,
            "scaled_max": scaled_max,
            "scale_factor": scale_factor,
            "scale_source": scale_source,
            "input_unit": "raw_grid",
            "output_unit": "Gy",
        }
            
        # 数据转为(Z,Y,X)；origin保持(X,Y,Z)，spacing返回为[Z,Y,X]
        dose_array = np.transpose(dose_array, (2, 1, 0))
        origin_xyz = np.array([origin[0], origin[1], origin[2]])
        spacing_zyx = np.array([spacing[2], spacing[1], spacing[0]])
            
        return dose_array, origin_xyz, spacing_zyx