import numpy as np
import nibabel as nib
import SimpleITK as sitk
import pydicom
import os
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.ticker import MultipleLocator
from typing import Tuple, Optional

def load_dicomdata(ct_folder: str):
    """读取RTSTRUCT所对应DICOM CT的几何参数"""
    ct_files = [os.path.join(ct_folder, f) for f in os.listdir(ct_folder) if "CT." in f and f.endswith(".dcm")]
    if not ct_files:
        raise FileNotFoundError(f"未在 {ct_folder} 找到CT DICOM文件")

    dsets = [pydicom.dcmread(fp, stop_before_pixels=True) for fp in ct_files]
    ds_ref = dsets[0]
    ct_orientation = np.array(ds_ref.ImageOrientationPatient, dtype=float)
    row_dir = ct_orientation[:3] / np.linalg.norm(ct_orientation[:3])
    col_dir = ct_orientation[3:] / np.linalg.norm(ct_orientation[3:])
    slice_dir = np.cross(row_dir, col_dir)
    slice_dir = slice_dir / np.linalg.norm(slice_dir)

    # 斜扫时不能按世界坐标z排序，需沿切片法向方向排序。
    dsets = sorted(
        dsets,
        key=lambda ds: float(np.dot(np.array(ds.ImagePositionPatient, dtype=float), slice_dir)),
    )

    ds0 = dsets[0]
    ct_origin = np.array(ds0.ImagePositionPatient, dtype=float)  # [x, y, z]
    spacing_xy = np.array(ds0.PixelSpacing, dtype=float)

    if len(dsets) > 1:
        pos0 = np.array(dsets[0].ImagePositionPatient, dtype=float)
        pos1 = np.array(dsets[1].ImagePositionPatient, dtype=float)
        spacing_z = float(abs(np.dot(pos1 - pos0, slice_dir)))
        if spacing_z <= 1e-6:
            spacing_z = float(getattr(ds0, "SliceThickness", 1.0))
    else:
        spacing_z = float(getattr(ds0, "SliceThickness", 1.0))

    # 与view_rt_dcm_files一致，使用[z, y, x]
    ct_spacing = np.array([spacing_z, spacing_xy[0], spacing_xy[1]], dtype=float)
    return ct_origin, ct_spacing, ct_orientation


def load_roi_reference_geometry(ct_folder: str):
    """兼容旧接口命名：读取RTSTRUCT对应CT的几何参数。"""
    return load_dicomdata(ct_folder)


def load_structures(rs_file: str):
    """读取 RTSTRUCT，提取 ROI 及轮廓点。"""
    ds = pydicom.dcmread(rs_file)
    rois = {}

    roi_numbers = {}
    if hasattr(ds, "ReferencedROISequence"):
        for ref_roi in ds.ReferencedROISequence:
            roi_num = int(ref_roi.ReferencedROINumber)
            roi_name = ref_roi.ReferencedROIName
            roi_numbers[roi_num] = roi_name

    if hasattr(ds, "ROIContourSequence"):
        for roi_contour in ds.ROIContourSequence:
            roi_num = int(roi_contour.ReferencedROINumber)
            roi_name = roi_numbers.get(roi_num, f"ROI_{roi_num}")

            display_color = None
            if hasattr(roi_contour, "ROIDisplayColor"):
                color_vals = roi_contour.ROIDisplayColor
                if len(color_vals) >= 3:
                    display_color = tuple(float(c) / 255.0 for c in color_vals[:3])

            contours = []
            if hasattr(roi_contour, "ContourSequence"):
                for contour in roi_contour.ContourSequence:
                    if hasattr(contour, "ContourData"):
                        contour_data = contour.ContourData
                        points = np.array(contour_data).reshape(-1, 3)
                        contours.append(points)

            rois[roi_num] = {
                "name": roi_name,
                "displayColor": display_color,
                "contours": contours,
            }

    return {"rois": rois}


def extract_slices(ct_array, dose_on_ct, z_idx: Optional[int] = None, y_idx: Optional[int] = None, x_idx: Optional[int] = None):
    """非交互地选择三个轴位索引，默认取中间层。"""
    z_default = ct_array.shape[0] // 2
    y_default = ct_array.shape[1] // 2
    x_default = ct_array.shape[2] // 2

    z_mid = z_default if z_idx is None else int(z_idx)
    y_mid = y_default if y_idx is None else int(y_idx)
    x_mid = x_default if x_idx is None else int(x_idx)

    z_mid = max(0, min(z_mid, ct_array.shape[0] - 1))
    y_mid = max(0, min(y_mid, ct_array.shape[1] - 1))
    x_mid = max(0, min(x_mid, ct_array.shape[2] - 1))

    print("=" * 60)
    print(f"✓ Axial (Z={z_mid}): ct {ct_array[z_mid].shape}, dose {dose_on_ct[z_mid].shape}")
    print(f"✓ Coronal (Y={y_mid}): ct {ct_array[:, y_mid, :].shape}, dose {dose_on_ct[:, y_mid, :].shape}")
    print(f"✓ Sagittal (X={x_mid}): ct {ct_array[:, :, x_mid].shape}, dose {dose_on_ct[:, :, x_mid].shape}")

    return z_mid, y_mid, x_mid


def resample(ct_array, ct_origin, ct_spacing, dose_array, dose_origin, dose_spacing, ct_affine=None, dose_affine=None):
    # 重采样
    
    # 创建SimpleITK图像
    ct_image = sitk.GetImageFromArray(ct_array)
    ct_image.SetOrigin(tuple(float(v) for v in ct_origin))
    # SimpleITK需要(X,Y,Z)顺序，这里把[Z,Y,X]转换为[X,Y,Z]
    ct_image.SetSpacing((float(ct_spacing[2]), float(ct_spacing[1]), float(ct_spacing[0])))
    
    # 从affine矩阵设置方向矩阵（处理坐标轴翻转）
    if ct_affine is not None:
        ct_rotation = ct_affine[:3, :3]
        ct_direction = []
        for i in range(3):
            col = ct_rotation[:, i]
            ct_direction.extend(col / np.linalg.norm(col))
        ct_image.SetDirection(ct_direction)
    
    dose_image = sitk.GetImageFromArray(dose_array)
    dose_image.SetOrigin(tuple(float(v) for v in dose_origin))
    dose_image.SetSpacing((float(dose_spacing[2]), float(dose_spacing[1]), float(dose_spacing[0])))
    
    if dose_affine is not None:
        dose_rotation = dose_affine[:3, :3]
        dose_direction = []
        for i in range(3):
            col = dose_rotation[:, i]
            dose_direction.extend(col / np.linalg.norm(col))
        dose_image.SetDirection(dose_direction)

    # 重采样到CT图像的空间
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(ct_image)
    resampler.SetInterpolator(sitk.sitkLinear)
    dose_on_ct_sitk = resampler.Execute(dose_image)
    dose_on_ct = sitk.GetArrayFromImage(dose_on_ct_sitk)

    return ct_image, dose_image, dose_on_ct_sitk, dose_on_ct


def _build_canvas_slice(ct_slice, dose_slice, plane_masks, canvas_h_mm, canvas_w_mm, row_mm, col_mm, vmin):
    """为单个切面构建 canvas，padding 到统一尺寸。"""
    target_h = int(np.round(canvas_h_mm / row_mm))
    target_w = int(np.round(canvas_w_mm / col_mm))

    ct_padded = _pad_center_2d(ct_slice, target_h, target_w, vmin)
    dose_padded = _pad_center_2d(dose_slice, target_h, target_w, 0.0)
    masks_padded = {
        roi_num: _pad_center_2d(mask_2d.astype(np.uint8), target_h, target_w, 0).astype(bool)
        for roi_num, mask_2d in plane_masks.items()
    }
    return ct_padded, dose_padded, masks_padded


def patient_to_pixel_coords(
    patient_coords: np.ndarray,
    ct_origin: np.ndarray,
    ct_spacing: np.ndarray,
    ct_shape: Tuple[int, int, int],
    ct_orientation: Optional[np.ndarray]
) -> np.ndarray:
    # 把患者坐标（mm）转换为 CT 图像的像素坐标。

    relative = patient_coords - ct_origin[np.newaxis, :]

    if ct_orientation is not None and len(ct_orientation) >= 6:
        row_dir = np.array(ct_orientation[:3], dtype=float)
        col_dir = np.array(ct_orientation[3:6], dtype=float)
        row_norm = np.linalg.norm(row_dir)
        col_norm = np.linalg.norm(col_dir)
        if row_norm > 0 and col_norm > 0:
            row_dir = row_dir / row_norm
            col_dir = col_dir / col_norm
            slice_dir = np.cross(row_dir, col_dir)
            slice_norm = np.linalg.norm(slice_dir)
            if slice_norm > 0:
                slice_dir = slice_dir / slice_norm

                # DICOM: 行方向对应列索引，列方向对应行索引；最终输出 [z, y, x]
                x_pix = np.dot(relative, row_dir) / float(ct_spacing[2])
                y_pix = np.dot(relative, col_dir) / float(ct_spacing[1])
                z_pix = np.dot(relative, slice_dir) / float(ct_spacing[0])
                return np.column_stack([z_pix, y_pix, x_pix])

    # 回退路径：方向信息不可用时按轴对齐处理。
    pixel_coords = np.column_stack([
        relative[:, 2] / ct_spacing[0],
        relative[:, 1] / ct_spacing[1],
        relative[:, 0] / ct_spacing[2],
    ])
    return pixel_coords


def build_roi_masks(rois, ct_shape, ct_origin, ct_spacing, ct_orientation, roi_map):
    """将RTSTRUCT轮廓栅格化为3D掩膜，便于任意轴位切片显示真实轮廓。"""
    roi_masks = {}
    for roi_num in roi_map:
        if roi_num not in rois:
            continue

        mask_3d = np.zeros(ct_shape, dtype=bool)
        for contour in rois[roi_num]['contours']:
            if len(contour) < 3:
                continue

            pix = patient_to_pixel_coords(contour, ct_origin, ct_spacing, ct_shape, ct_orientation)
            z_idx = int(round(float(np.mean(pix[:, 0]))))
            if z_idx < 0 or z_idx >= ct_shape[0]:
                continue

            poly_yx = pix[:, [1, 2]]
            y_min = max(int(np.floor(np.min(poly_yx[:, 0]))), 0)
            y_max = min(int(np.ceil(np.max(poly_yx[:, 0]))), ct_shape[1] - 1)
            x_min = max(int(np.floor(np.min(poly_yx[:, 1]))), 0)
            x_max = min(int(np.ceil(np.max(poly_yx[:, 1]))), ct_shape[2] - 1)
            if y_min > y_max or x_min > x_max:
                continue

            yy, xx = np.mgrid[y_min:y_max + 1, x_min:x_max + 1]
            points_xy = np.column_stack((xx.ravel(), yy.ravel()))
            poly_xy = np.column_stack((poly_yx[:, 1], poly_yx[:, 0]))
            inside = Path(poly_xy).contains_points(points_xy).reshape(yy.shape)
            mask_3d[z_idx, y_min:y_max + 1, x_min:x_max + 1] |= inside

        if np.any(mask_3d):
            roi_masks[roi_num] = mask_3d

    return roi_masks


def _pad_center_2d(arr, target_h, target_w, fill_value):
    """中心填充数组到目标尺寸。"""
    h, w = arr.shape
    target_h = max(target_h, h)
    target_w = max(target_w, w)
    pad_h = target_h - h
    pad_w = target_w - w
    top = pad_h // 2
    bottom = pad_h - top
    left = pad_w // 2
    right = pad_w - left
    return np.pad(arr, ((top, bottom), (left, right)),
                   mode='constant', constant_values=fill_value)
