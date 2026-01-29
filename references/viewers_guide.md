# Browser-Based Viewer Guide

This reference covers using OHIF and SLIM viewers for quick visualization of IDC imaging data without downloads.

## When to Use Viewers

| Scenario | Best Approach |
|----------|---------------|
| Quick preview of data | Viewers |
| Share imaging with collaborators | Viewer URL |
| Detailed analysis | Download + local tools |
| Machine learning input | Download + Python |
| Clinical review prototype | Viewers |

**Key Point:** Viewers are for visualization. For programmatic access, use idc-index or DICOMweb.

## Recommended: Using get_viewer_URL()

The `idc-index` package provides a `get_viewer_URL()` method that automatically selects the appropriate viewer (OHIF for radiology, SLIM for slide microscopy):

```python
from idc_index import IDCClient
import webbrowser

client = IDCClient()

# Query for series
results = client.sql_query("""
    SELECT SeriesInstanceUID, StudyInstanceUID, Modality
    FROM index
    WHERE collection_id = 'rider_pilot' AND Modality = 'CT'
    LIMIT 1
""")

# Get viewer URL for a series (auto-selects OHIF or SLIM)
viewer_url = client.get_viewer_URL(seriesInstanceUID=results.iloc[0]['SeriesInstanceUID'])
print(viewer_url)
webbrowser.open(viewer_url)

# Or view entire study (all series in one view)
viewer_url = client.get_viewer_URL(studyInstanceUID=results.iloc[0]['StudyInstanceUID'])
print(viewer_url)
```

This method is preferred because it:
- Automatically selects OHIF v3 for radiology or SLIM for slide microscopy
- Handles URL encoding correctly
- Works with both series and study UIDs

## OHIF Viewer (Radiology)

The OHIF Viewer is for standard radiology imaging: CT, MR, PET, X-ray, etc.

### URL Pattern (Manual Construction)

If you need to construct URLs manually (e.g., for documentation or sharing):

```
https://viewer.imaging.datacommons.cancer.gov/viewer/{StudyInstanceUID}
```

### Supported Modalities

- CT (Computed Tomography)
- MR (Magnetic Resonance)
- PET (Positron Emission Tomography)
- CR (Computed Radiography)
- DX (Digital Radiography)
- NM (Nuclear Medicine)
- US (Ultrasound)
- XA (X-ray Angiography)

### Example URLs

```python
# Single study
study_uid = "1.3.6.1.4.1.14519.5.2.1.6279.6001.298806137288633453246975630178"
url = f"https://viewer.imaging.datacommons.cancer.gov/viewer/{study_uid}"

# This opens the OHIF viewer with all series in the study
print(url)
```

### Generate Viewer URLs from Query

```python
from idc_index import IDCClient

client = IDCClient()

# Find CT chest studies
df = client.sql_query("""
    SELECT DISTINCT StudyInstanceUID, PatientID,
           collection_id, StudyDescription
    FROM index
    WHERE Modality = 'CT'
    AND BodyPartExamined = 'CHEST'
    AND series_size_MB < 100
    LIMIT 5
""")

# Generate viewer URLs
base_url = "https://viewer.imaging.datacommons.cancer.gov/viewer"
for _, row in df.iterrows():
    study_uid = row['StudyInstanceUID']
    print(f"Study: {row.get('StudyDescription', 'N/A')}")
    print(f"  {base_url}/{study_uid}")
    print()
```

## SLIM Viewer (Microscopy)

The SLIM Viewer is for slide microscopy (pathology) images.

### URL Pattern

```
https://viewer.imaging.datacommons.cancer.gov/slim/studies/{StudyInstanceUID}
```

### Supported Modalities

- SM (Slide Microscopy)
- Whole slide imaging (WSI)

### Finding Microscopy Studies

```python
from idc_index import IDCClient

client = IDCClient()

# Find slide microscopy studies
df = client.sql_query("""
    SELECT DISTINCT StudyInstanceUID, PatientID,
           collection_id, series_size_MB
    FROM index
    WHERE Modality = 'SM'
    LIMIT 5
""")

# Generate SLIM viewer URLs
base_url = "https://viewer.imaging.datacommons.cancer.gov/slim/studies"
for _, row in df.iterrows():
    study_uid = row['StudyInstanceUID']
    print(f"Collection: {row['collection_id']}")
    print(f"  {base_url}/{study_uid}")
    print()
```

## Complete Workflow: Query to Viewer

```python
# /// script
# dependencies = [
#   "idc-index"
# ]
# ///

from idc_index import IDCClient
import webbrowser

client = IDCClient()

# Step 1: Find relevant series
df = client.sql_query("""
    SELECT
        SeriesInstanceUID,
        StudyInstanceUID,
        collection_id,
        Modality,
        BodyPartExamined,
        PatientID
    FROM index
    WHERE Modality = 'MR'
    AND BodyPartExamined = 'BRAIN'
    AND series_size_MB < 50
    LIMIT 5
""")

# Step 2: Generate viewer URLs using get_viewer_URL() (recommended)
print("Brain MR Series Available for Viewing:\n")
for _, row in df.iterrows():
    viewer_url = client.get_viewer_URL(seriesInstanceUID=row['SeriesInstanceUID'])
    print(f"Patient: {row['PatientID']}")
    print(f"Collection: {row['collection_id']}")
    print(f"URL: {viewer_url}")
    print()
    # webbrowser.open(viewer_url)  # Uncomment to open automatically
```

## Viewer Features

### OHIF Viewer

- Multi-planar reconstruction (MPR)
- Window/level adjustment
- Zoom, pan, scroll
- Measurement tools (length, area)
- Series comparison (multi-viewport)
- Annotation overlays
- DICOM header inspection

### SLIM Viewer

- Multi-resolution zoom (pyramidal images)
- Pan and navigate large slides
- Annotation display
- Region of interest selection
- Multiple channels/stains

## Limitations

### OHIF Viewer

- Requires study to be in current IDC version
- Performance depends on network speed
- Some advanced rendering features may be limited
- No offline access

### SLIM Viewer

- Large slides may take time to load
- Optimized for slide microscopy only
- Limited annotation editing

## Alternatives

For advanced analysis beyond viewer capabilities:

| Need | Solution |
|------|----------|
| 3D rendering | Download + 3D Slicer |
| Segmentation | Download + ITK-SNAP |
| Batch processing | Download + Python |
| AI/ML workflows | Download + framework |
| Custom measurements | Download + pydicom |

## Viewer URL Reference

| Viewer | URL Pattern | Use Case |
|--------|-------------|----------|
| OHIF | `viewer.imaging.datacommons.cancer.gov/viewer/{StudyUID}` | Radiology |
| SLIM | `viewer.imaging.datacommons.cancer.gov/slim/studies/{StudyUID}` | Microscopy |

## Resources

- [OHIF Viewer Documentation](https://docs.ohif.org/)
- [SLIM Viewer Documentation](https://github.com/ImagingDataCommons/slim)
- [IDC Portal](https://portal.imaging.datacommons.cancer.gov/) - Browse with integrated viewers
