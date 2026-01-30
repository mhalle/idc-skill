# Analysis Pipeline Integration

This reference covers integrating IDC data with common analysis tools and workflows.

## pydicom: Reading DICOM Files

### Basic Usage

```python
import pydicom
from pathlib import Path

# Read single file
dcm = pydicom.dcmread('image.dcm')

# Access common attributes
print(dcm.PatientID)
print(dcm.Modality)
print(dcm.SeriesDescription)

# Access pixel data
pixels = dcm.pixel_array  # numpy array
print(f"Shape: {pixels.shape}, dtype: {pixels.dtype}")
```

### Processing a Series

```python
from pathlib import Path
import numpy as np
import pydicom

def load_series(series_dir):
    """Load all DICOM files in a directory as sorted slices."""
    files = list(Path(series_dir).glob('*.dcm'))
    slices = [pydicom.dcmread(str(f)) for f in files]

    # Sort by slice position (for CT/MR)
    slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))

    # Stack into 3D array
    volume = np.stack([s.pixel_array for s in slices])
    return volume, slices[0]  # Return volume and first slice for metadata

volume, meta = load_series('./data/ct_series')
print(f"Volume: {volume.shape}")  # (slices, rows, cols)
print(f"Spacing: {meta.PixelSpacing}, {meta.SliceThickness}")
```

### Applying Rescale (CT Hounsfield Units)

```python
def get_hu_volume(series_dir):
    """Load CT series and convert to Hounsfield Units."""
    files = sorted(Path(series_dir).glob('*.dcm'))
    slices = [pydicom.dcmread(str(f)) for f in files]
    slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))

    volume = np.stack([s.pixel_array for s in slices]).astype(np.float32)

    # Apply rescale
    slope = slices[0].RescaleSlope
    intercept = slices[0].RescaleIntercept
    volume = volume * slope + intercept

    return volume

hu_volume = get_hu_volume('./data/ct_series')
# Typical HU ranges: air=-1000, water=0, bone=400-1000
```

## SimpleITK: Advanced Image Processing

### Loading DICOM Series

```python
import SimpleITK as sitk

series_path = "./data/ct_series"
reader = sitk.ImageSeriesReader()
dicom_names = reader.GetGDCMSeriesFileNames(series_path)
reader.SetFileNames(dicom_names)
image = reader.Execute()

print(f"Size: {image.GetSize()}")  # (x, y, z)
print(f"Spacing: {image.GetSpacing()}")  # mm
print(f"Origin: {image.GetOrigin()}")
```

### Common Processing Operations

```python
# Resample to isotropic spacing
def resample_isotropic(image, new_spacing=[1.0, 1.0, 1.0]):
    original_spacing = image.GetSpacing()
    original_size = image.GetSize()

    new_size = [
        int(round(osz * ospc / nspc))
        for osz, ospc, nspc in zip(original_size, original_spacing, new_spacing)
    ]

    return sitk.Resample(
        image, new_size, sitk.Transform(),
        sitk.sitkLinear, image.GetOrigin(),
        new_spacing, image.GetDirection(), 0.0,
        image.GetPixelID()
    )

# Apply smoothing
smoothed = sitk.CurvatureFlow(image, timeStep=0.125, numberOfIterations=5)

# Threshold (e.g., lung segmentation)
binary = sitk.BinaryThreshold(image, lowerThreshold=-1000, upperThreshold=-400)

# Save as NIfTI
sitk.WriteImage(image, "volume.nii.gz")
```

### Registration Example

```python
# Register moving image to fixed image
fixed = sitk.ReadImage("fixed.nii.gz")
moving = sitk.ReadImage("moving.nii.gz")

registration = sitk.ImageRegistrationMethod()
registration.SetMetricAsMeanSquares()
registration.SetOptimizerAsGradientDescent(
    learningRate=1.0, numberOfIterations=100
)
registration.SetInitialTransform(sitk.TranslationTransform(3))
registration.SetInterpolator(sitk.sitkLinear)

transform = registration.Execute(fixed, moving)
registered = sitk.Resample(moving, fixed, transform)
```

## Complete Workflow: IDC to Analysis

```python
# /// script
# dependencies = [
#   "idc-index",
#   "pydicom",
#   "SimpleITK",
#   "numpy"
# ]
# ///

from idc_index import IDCClient
import SimpleITK as sitk
from pathlib import Path

# 1. Query IDC for small chest CT
client = IDCClient()
df = client.sql_query("""
    SELECT SeriesInstanceUID, PatientID, series_size_MB
    FROM index
    WHERE Modality = 'CT'
    AND BodyPartExamined = 'CHEST'
    AND series_size_MB < 50
    LIMIT 1
""")

series_uid = df['SeriesInstanceUID'].iloc[0]
print(f"Downloading: {series_uid}")

# 2. Download
client.download_from_selection(
    seriesInstanceUID=[series_uid],
    downloadDir="./data",
    dirTemplate="%SeriesInstanceUID"
)

# 3. Load with SimpleITK
series_path = f"./data/{series_uid}"
reader = sitk.ImageSeriesReader()
dicom_names = reader.GetGDCMSeriesFileNames(series_path)
reader.SetFileNames(dicom_names)
image = reader.Execute()

print(f"Loaded: {image.GetSize()}")

# 4. Process (example: lung window)
# Lung window: center=-600, width=1500
lower = -600 - 750  # -1350
upper = -600 + 750  # 150
windowed = sitk.IntensityWindowing(image, lower, upper, 0, 255)

# 5. Save
sitk.WriteImage(sitk.Cast(windowed, sitk.sitkUInt8), "lung_window.nii.gz")
print("Saved lung_window.nii.gz")
```

## Pathology: Slide Microscopy

For whole slide images (SM modality), use specialized libraries:

```python
# Query for slide microscopy
df = client.sql_query("""
    SELECT SeriesInstanceUID, collection_id
    FROM index
    WHERE Modality = 'SM'
    LIMIT 5
""")

# Download (WSI files are large - check size first!)
client.fetch_index("sm_index")
sm_info = client.sql_query("""
    SELECT SeriesInstanceUID,
           ObjectiveLensPower,
           min_PixelSpacing_2sf as resolution_mm
    FROM sm_index
    LIMIT 5
""")
```

For WSI analysis, consider:
- **openslide**: Reading various WSI formats
- **histolab**: Tile extraction and preprocessing
- **pathml**: Full computational pathology toolkit

## Radiomics Features

```python
# /// script
# dependencies = ["pyradiomics", "SimpleITK"]
# ///

from radiomics import featureextractor
import SimpleITK as sitk

# Load image and mask
image = sitk.ReadImage("ct_volume.nii.gz")
mask = sitk.ReadImage("tumor_mask.nii.gz")

# Extract features
extractor = featureextractor.RadiomicsFeatureExtractor()
features = extractor.execute(image, mask)

# Print first-order features
for key, val in features.items():
    if 'firstorder' in key:
        print(f"{key}: {val}")
```

## Tips

- **Check series_size_MB before downloading** - Some series are very large
- **Use LIMIT in queries** when testing workflows
- **Verify modality-specific handling** - CT, MR, PT, SM all have different conventions
- **Check license_short_name** before using data in publications
