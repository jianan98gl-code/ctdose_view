"""Canvas和数据处理"""
import numpy as np
from typing import Dict, Tuple


def _pad_center_2d(arr: np.ndarray, target_h: int, target_w: int, fill_value: float) -> np.ndarray:
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
    return np.pad(arr, ((top, bottom), (left, right)), mode="constant", constant_values=fill_value)


def compute_canvas_geometry(ct_array: np.ndarray,
                           ct_spacing: np.ndarray,
                           z_idx: int,
                           y_idx: int,
                           x_idx: int) -> Tuple[float, float, float]:
    """计算canvas尺寸（mm）和纵横比。
    
    Parameters:
        ct_array: CT图像数组
        ct_spacing: CT间距 [z, y, x]
        z_idx, y_idx, x_idx: 切面索引
    
    Returns:
        Tuple[canvas_w_mm, canvas_h_mm, canvas_box_aspect]:
            - canvas_w_mm: Canvas宽度（mm）
            - canvas_h_mm: Canvas高度（mm）
            - canvas_box_aspect: 纵横比
    """
    sz, sy, sx = ct_spacing
    
    axial_h_mm = ct_array[z_idx].shape[0] * sy
    axial_w_mm = ct_array[z_idx].shape[1] * sx
    coronal_h_mm = ct_array[:, y_idx, :].shape[0] * sz
    coronal_w_mm = ct_array[:, y_idx, :].shape[1] * sx
    sagittal_h_mm = ct_array[:, :, x_idx].shape[0] * sz
    sagittal_w_mm = ct_array[:, :, x_idx].shape[1] * sy
    
    ct_mip = np.max(ct_array, axis=0)
    mip_h_mm = ct_mip.shape[0] * sy
    mip_w_mm = ct_mip.shape[1] * sx

    canvas_w_mm = max(axial_w_mm, coronal_w_mm, sagittal_w_mm, mip_w_mm)
    canvas_h_mm = max(axial_h_mm, coronal_h_mm, sagittal_h_mm, mip_h_mm)
    canvas_box_aspect = canvas_h_mm / canvas_w_mm if canvas_w_mm else 1.0

    return canvas_w_mm, canvas_h_mm, canvas_box_aspect


def prepare_plane_slices(ct_array: np.ndarray,
                        dose_on_ct: np.ndarray,
                        roi_masks: Dict[int, np.ndarray],
                        z_idx: int,
                        y_idx: int,
                        x_idx: int,
                        vmin: float,
                        vmax: float) -> Dict[str, Tuple]:
    """提取4个切面的CT、剂量和ROI掩膜数据。
    
    Parameters:
        ct_array: CT图像数组
        dose_on_ct: 剂量数组
        roi_masks: ROI掩膜字典
        z_idx, y_idx, x_idx: 切面索引
        vmin, vmax: CT显示范围
    
    Returns:
        Dict with keys 'axial', 'coronal', 'sagittal', 'mip':
            Each value is (ct_slice, dose_slice, plane_masks)
    """
    axial_masks = {roi_num: mask[z_idx] for roi_num, mask in roi_masks.items()}
    coronal_masks = {roi_num: mask[:, y_idx, :] for roi_num, mask in roi_masks.items()}
    sagittal_masks = {roi_num: mask[:, :, x_idx] for roi_num, mask in roi_masks.items()}
    mip_masks = {roi_num: np.max(mask, axis=0) for roi_num, mask in roi_masks.items()}

    ct_mip = np.clip(np.max(ct_array, axis=0), vmin, vmax)
    dose_mip = np.max(dose_on_ct, axis=0)

    return {
        'axial': (np.clip(ct_array[z_idx], vmin, vmax), dose_on_ct[z_idx], axial_masks),
        'coronal': (np.clip(ct_array[:, y_idx, :], vmin, vmax), dose_on_ct[:, y_idx, :], coronal_masks),
        'sagittal': (np.clip(ct_array[:, :, x_idx], vmin, vmax), dose_on_ct[:, :, x_idx], sagittal_masks),
        'mip': (ct_mip, dose_mip, mip_masks),
    }


def build_canvas_slice(ct_slice: np.ndarray,
                      dose_slice: np.ndarray,
                      plane_masks: Dict[int, np.ndarray],
                      canvas_h_mm: float,
                      canvas_w_mm: float,
                      row_mm: float,
                      col_mm: float,
                      vmin: float) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """为单个切面构建canvas，padding到统一尺寸。
    
    Parameters:
        ct_slice: CT切面
        dose_slice: 剂量切面
        plane_masks: 该切面的ROI掩膜
        canvas_h_mm, canvas_w_mm: Canvas目标尺寸
        row_mm, col_mm: 像素间距
        vmin: CT填充值
    
    Returns:
        Tuple[ct_padded, dose_padded, masks_padded]:
            三个都padding到canvas尺寸
    """
    target_h = int(np.round(canvas_h_mm / row_mm))
    target_w = int(np.round(canvas_w_mm / col_mm))

    ct_padded = _pad_center_2d(ct_slice, target_h, target_w, vmin)
    dose_padded = _pad_center_2d(dose_slice, target_h, target_w, 0.0)
    masks_padded = {
        roi_num: _pad_center_2d(mask_2d.astype(np.uint8), target_h, target_w, 0).astype(bool)
        for roi_num, mask_2d in plane_masks.items()
    }
    return ct_padded, dose_padded, masks_padded
