'''
读取NIfTI文件的工具类，提供了两个静态方法：
1. load_ct_nifti(ct_nii_file): 读取CT NIfTI文件
2. load_dose_nifti(dose_nii_file): 读取剂量 NIfTI文件
每个方法都返回图像数据数组、原点坐标、像素间距
'''

import numpy as np
import nibabel as nib

class ReadNifti:
    def __init__(self):
        pass

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

    def load_dose_nifti(self, dose_nii_file: str):
        img = nib.load(dose_nii_file)
        dose_array = img.get_fdata().astype(np.float32)
        origin, spacing = self._extract_affine_info(img.affine)

        # 剂量单位校正
        if dose_array.max() > 500:
            dose_array = dose_array / 10000.0
            
        # 数据转为(Z,Y,X)；origin保持(X,Y,Z)，spacing返回为[Z,Y,X]
        dose_array = np.transpose(dose_array, (2, 1, 0))
        origin_xyz = np.array([origin[0], origin[1], origin[2]])
        spacing_zyx = np.array([spacing[2], spacing[1], spacing[0]])
            
        return dose_array, origin_xyz, spacing_zyx