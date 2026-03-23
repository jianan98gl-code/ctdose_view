# CT + 剂量 + ROI 可视化工具

一个用于放射肿瘤学影像处理的综合可视化工具，将CT扫描、放射治疗剂量分布和肿瘤/器官轮廓（ROI）整合在一个诊断图中。

##  功能

-  **多格式医学影像支持**：NIfTI格式CT和剂量数据
-  **自动配准与重采样**：将剂量分布与CT图像对齐
-  **灵活的ROI标注**：支持自定义颜色、线宽和ROI选择
-  **四面板输出**：轴向、冠状、矢状切片 + MIP投影
-  **配置驱动**：YAML配置文件或命令行参数完全控制
-  **适用场景**：
  - 头颈部肿瘤放射治疗计划评估
  - 剂量分布验证
  - 器官保护效果监测


### 系统要求
- Python 3.7+
- 操作系统：Windows / Linux / macOS

### Python依赖包

```
nibabel>=3.2.0          # NIfTI医学影像读取
pydicom>=2.1.0          # DICOM格式处理
matplotlib>=3.3.0       # 图像渲染和保存
numpy>=1.19.0           # 数据处理和重采样
PyYAML>=5.3.0           # YAML配置文件解析
scipy>=1.5.0            # 插值和数学运算
```

##  安装

### 方法1：使用pip

```bash
# 克隆或下载项目
cd view_ctdose

# 创建虚拟环境（可选但推荐）
python -m venv venv
source venv/bin/activate          # Linux/macOS
venv\Scripts\activate             # Windows

# 安装依赖
pip install -r requirements.txt
# 如果没有requirements.txt，手动安装：
pip install nibabel pydicom matplotlib numpy PyYAML scipy
```

### 方法2：使用Conda

```bash
conda create -n ct_dose_viewer python=3.9
conda activate ct_dose_viewer
conda install -c conda-forge nibabel pydicom matplotlib numpy pyyaml scipy
```

##  快速开始

### 1. 准备数据文件

需要以下文件：
- **CT图像** - NIfTI格式 (`.nii` 或 `.nii.gz`)
- **剂量分布** - NIfTI格式 (`.nii` 或 `.nii.gz`)
- **ROI结构集** - DICOM结构集文件 (`RS.*.dcm`)
- **计划剂量** - DICOM剂量文件 (`RD.*.dcm`) - 用于提取DoseGridScaling
- **DICOM原始数据** - 用于提取ROI参考几何信息的DICOM目录

### 2. 配置config.yaml

在 `viewer/` 目录下编辑 `config.yaml`，设置数据路径和显示参数：

```yaml
# 输入数据路径（支持相对路径或绝对路径）
ct_nii: "path/to/your/CT.nii"
dose_nii: "path/to/your/dose.nii"
rs_dcm: "path/to/your/RS.*.dcm"
ct_dicom_dir: "path/to/DICOM/directory"
rd_dcm: "path/to/your/RD.*.dcm"

# 输出文件路径
output: "./output/ct_dose_roi_four_panel.png"

# 图像标题
title: "Your Case Title - Dose Distribution"

# 要显示的ROI ID列表
roi_ids: [1, 2, 3, 4, 5]

# ROI ID到名称的映射
roi_map:
  1: "GTV"
  2: "CTV"
  3: "PTV"
  4: "Organ_A"
  5: "Organ_B"

# ROI显示颜色
roi_colors:
  GTV: red
  CTV: green
  PTV: cyan
  Organ_A: yellow
  Organ_B: magenta

# ROI轮廓线宽（像素）
roi_linewidths:
  GTV: 2.5
  CTV: 1.8
  PTV: 1.5
  Organ_A: 1.5
  Organ_B: 1.5

# 剂量显示阈值（相对于最大剂量的比例，范围0-1）
dose_threshold_ratio: 0.1

# 剂量缩放策略（"dicom_or_config" 或 "raw"）
scaling_policy: dicom_or_config

# 输出图像分辨率（DPI）
dpi: 150

# 可选：指定切片位置（不填则自动取中心）
# z_idx: 120
# y_idx: 180
# x_idx: 160
```

### 3. 运行程序

#### 使用配置文件（推荐）

```bash
cd viewer
python main.py --config config.yaml
```

#### 命令行参数覆盖

```bash
python main.py \
  --config config.yaml \
  --ct_nii path/to/CT.nii \
  --dose_nii path/to/dose.nii \
  --output path/to/output.png
```

#### 环境变量配置

```bash
# 设置剂量缩放因子
export DOSE_SCALE_FACTOR=0.0001
python main.py --config config.yaml
```

##  使用示例

### 示例1：基础用法

```bash
# 假设数据文件都在 data/ 目录下
cd viewer
python main.py --config config.yaml
```

### 示例2：只显示特定ROI

```bash
python main.py \
  --config config.yaml \
  --roi_ids [45,43,41,40]  # 只显示这四个ROI
```

### 示例3：自定义输出路径和分辨率

```bash
python main.py \
  --config config.yaml \
  --output ./results/case_20240323.png \
  --dpi 300
```

### 示例4：指定切片位置（而不是自动中心）

```bash
python main.py \
  --config config.yaml \
  --z_idx 120 \
  --y_idx 180 \
  --x_idx 160
```

##  输出说明

程序会生成一个四面板PNG图像：

| 面板 | 说明 |
|------|------|
| **左上** | 轴向(Axial)切片 + CT灰度 + 剂量热力图 + ROI轮廓 |
| **右上** | 冠状(Coronal)切片 + 同上 |
| **左下** | 矢状(Sagittal)切片 + 同上 |
| **右下** | 最大强度投影(MIP) + 同上 |

**图例说明：**
- 背景：CT图像（窗宽/窗位默认设置）
- 热力图：剂量分布（蓝→绿→黄→红表示剂量从低到高）
- 彩色轮廓：ROI结构

##  高级配置

### 剂量单位转换

如果DICOM文件中的DoseGridScaling不正确，可以通过环境变量手动设置：

```bash
export DOSE_SCALE_FACTOR=0.0001
python main.py --config config.yaml
```

### 修改CT窗宽/窗位

编辑 `ReadNifti.py` 中的默认窗口设置：

```python
# CT窗宽/窗位（Hounsfield单位）
WINDOW_CENTER = 40    # 默认
WINDOW_WIDTH = 400    # 默认
```

### 自定义色图

编辑 `visualization/_colormap.py` 中的剂量色图定义：

```python
# 修改dose_colormap来改变热力图颜色
```

##  常见问题

### Q1: 导入错误 "ModuleNotFoundError: No module named 'nibabel'"

**解决：** 确保已安装依赖包

```bash
pip install nibabel pydicom matplotlib numpy PyYAML scipy
```

### Q2: DICOM文件无法读取

**解决：** 检查以下几点：
- DICOM文件路径是否正确
- DICOM文件是否完整（未损坏）
- `ct_dicom_dir` 必须指向包含原始DICOM的目录（用于提取几何信息）

### Q3: ROI轮廓显示不全或偏移

**解决：** 检查以下内容：
- ROI ID是否与实际结构集中的ID匹配
- CT和DICOM的几何对齐是否正确
- 是否设置了正确的 `ct_dicom_dir` 路径

### Q4: 剂量值看起来不正确

**解决：** 检查剂量缩放策略：
- 使用 `scaling_policy: dicom_or_config` 尝试从DICOM提取缩放因子
- 或手动设置 `DOSE_SCALE_FACTOR` 环境变量

### Q5: 内存不足或处理很慢

**解决：** 尝试以下方案：
- 使用更低的输出分辨率 (`dpi: 100` 而不是 `300`)
- 指定特定切片位置而不是自动计算
- 减少 `roi_ids` 中的ROI数量

##  项目结构

```
view_ctdose/
├── viewer/                    # 主应用包
│   ├── main.py               # 程序入口
│   ├── config.yaml           # 配置文件（示例）
│   ├── ReadNifti.py          # NIfTI/DICOM读取模块
│   ├── cli_config.py         # 命令行参数处理
│   ├── roi_config.py         # ROI配置解析
│   ├── data_paths.py         # 数据路径解析
│   ├── utils.py              # 工具函数（重采样、掩膜生成等）
│   ├── visualization/        # 渲染模块
│   │   ├── __init__.py
│   │   ├── render.py         # 主渲染引擎
│   │   ├── canvas.py         # 几何计算和坐标变换
│   │   ├── layout.py         # 图布局管理
│   │   ├── _colormap.py      # 剂量色图定义
│   │   └── _contours.py      # ROI轮廓绘制
│   └── __init__.py
├── README.md                  # 本文件
└── requirements.txt           # Python依赖列表
```

##  配置参数详解

| 参数 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `ct_nii` | str | ✓ | CT图像NIfTI文件路径 | `"./data/CT.nii"` |
| `dose_nii` | str | ✓ | 剂量NIfTI文件路径 | `"./data/dose.nii"` |
| `rs_dcm` | str | ✓ | DICOM结构集文件路径 | `"./data/RS.dcm"` |
| `ct_dicom_dir` | str | ✓ | DICOM原始数据目录 | `"./data/DICOM/"` |
| `rd_dcm` | str | ✓ | DICOM计划剂量文件 | `"./data/RD.dcm"` |
| `output` | str | ✓ | 输出PNG文件路径 | `"./output.png"` |
| `title` | str | ✗ | 图像标题 | `"Patient Case 001"` |
| `roi_ids` | list | ✗ | 要显示的ROI ID列表 | `[1, 2, 3, 4]` |
| `roi_map` | dict | ✗ | ROI ID到名称的映射 | `{1: "GTV", ...}` |
| `roi_colors` | dict | ✗ | ROI显示颜色 | `{"GTV": "red", ...}` |
| `roi_linewidths` | dict | ✗ | ROI轮廓线宽 | `{"GTV": 2.5, ...}` |
| `dose_threshold_ratio` | float | ✗ | 剂量显示阈值(0-1) | `0.1` |
| `scaling_policy` | str | ✗ | 剂量缩放策略 | `"dicom_or_config"` |
| `z_idx`, `y_idx`, `x_idx` | int | ✗ | 切片位置索引 | `120`, `180`, `160` |
| `dpi` | int | ✗ | 输出分辨率 | `150` |

##  支持的数据格式

### 输入
- **医学影像**：NIfTI格式 (`.nii`, `.nii.gz`)
- **DICOM文件**：结构集 (RS), 计划剂量 (RD), 原始CT
- **坐标系**：LPS (Left-Posterior-Superior) 和 RAS (Right-Anterior-Superior) 自动转换

### 输出
- **图像格式**：PNG（高质量医学影像输出）
- **分辨率**：可配置 (默认 150 DPI)
