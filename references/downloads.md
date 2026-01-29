# Download Guide

This reference covers downloading DICOM data from IDC using idc-index.

## Primary Method: download_from_selection()

The `download_from_selection()` method is the recommended way to download data:

```python
from idc_index import IDCClient

client = IDCClient()

# Download entire collection
client.download_from_selection(
    collection_id="rider_pilot",
    downloadDir="./data/rider"
)

# Download specific series
series_uids = ["1.2.3...", "1.2.4..."]
client.download_from_selection(
    seriesInstanceUID=series_uids,
    downloadDir="./data/selected"
)

# Download by patient
client.download_from_selection(
    patientId="TCGA-05-4244",
    downloadDir="./data/patient"
)
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `collection_id` | Download entire collection(s) |
| `patientId` | Download by patient ID(s) |
| `studyInstanceUID` | Download by study UID(s) |
| `seriesInstanceUID` | Download by series UID(s) |
| `downloadDir` | Output directory |
| `dirTemplate` | Custom directory structure |

## Directory Templates

Control output directory structure with `dirTemplate`:

```python
# Default template
# %collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID

# Simplified hierarchy
client.download_from_selection(
    collection_id="tcga_luad",
    downloadDir="./data",
    dirTemplate="%collection_id/%PatientID/%Modality"
)
# Result: ./data/tcga_luad/TCGA-05-4244/CT/

# Flat structure (all files in one directory)
client.download_from_selection(
    seriesInstanceUID=series_uids,
    downloadDir="./data/flat",
    dirTemplate=""
)
# Result: ./data/flat/*.dcm

# Custom organization
client.download_from_selection(
    collection_id="nlst",
    downloadDir="./data",
    dirTemplate="%Modality/%collection_id/%PatientID"
)
```

### Available Template Variables

- `%collection_id` - IDC collection identifier
- `%PatientID` - Patient identifier
- `%StudyInstanceUID` - DICOM study UID
- `%SeriesInstanceUID` - DICOM series UID
- `%Modality` - Imaging modality

## Command-Line Download

The `idc download` command provides CLI access without writing Python:

```bash
# Download entire collection
idc download rider_pilot --download-dir ./data

# Download specific series by UID
idc download "1.3.6.1.4.1.9328.50.1.69736" --download-dir ./data

# Download multiple items (comma-separated)
idc download "tcga_luad,tcga_lusc" --download-dir ./data

# Download from manifest file
idc download manifest.txt --download-dir ./data

# Custom directory template
idc download nlst --download-dir ./data --dir-template "%Modality/%PatientID"
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--download-dir` | Output directory (default: current) |
| `--dir-template` | Directory structure template |
| `--log-level` | Verbosity: debug, info, warning, error |

## Manifest Files

Manifest files contain S3 URLs for reproducible downloads:

```
s3://idc-open-data/cb09464a-c5cc-4428-9339-d7fa87cfe837/*
s3://idc-open-data/88f3990d-bdef-49cd-9b2b-4787767240f2/*
```

### Generate manifest from query

```python
results = client.sql_query("""
    SELECT series_aws_url
    FROM index
    WHERE collection_id = 'rider_pilot' AND Modality = 'CT'
""")

# Save as manifest
with open('ct_manifest.txt', 'w') as f:
    for url in results['series_aws_url']:
        f.write(url + '\n')
```

Then download:
```bash
idc download ct_manifest.txt --download-dir ./ct_data
```

### Sources of manifests

- Export from IDC Portal after cohort selection
- Share with collaborators for reproducibility
- Generate programmatically from queries

## Batch Downloads

For large datasets, download in batches:

```python
results = client.sql_query("""
    SELECT SeriesInstanceUID
    FROM index
    WHERE collection_id = 'nlst' AND Modality = 'CT'
    LIMIT 100
""")

batch_size = 10
for i in range(0, len(results), batch_size):
    batch = results.iloc[i:i+batch_size]
    client.download_from_selection(
        seriesInstanceUID=list(batch['SeriesInstanceUID'].values),
        downloadDir=f"./data/batch_{i//batch_size}"
    )
```

## Estimating Download Size

Always check size before downloading:

```python
# Size for specific criteria
size_info = client.sql_query("""
    SELECT
        SUM(series_size_MB) as total_mb,
        COUNT(*) as series_count
    FROM index
    WHERE collection_id = 'nlst' AND Modality = 'CT'
""")
print(f"Total: {size_info['total_mb'].iloc[0]:.0f} MB ({size_info['series_count'].iloc[0]} series)")
```

## Troubleshooting

### Download fails with timeout

- Download smaller batches (10-20 series)
- Check network connection
- Implement retry logic

### 403 or S3 errors

- You may be in a restricted environment
- Use the three-step workflow: query → generate script → user runs locally

### Files won't open

- Check DICOM object type (some require specialized viewers)
- Verify with pydicom: `pydicom.dcmread(file, force=True)`
- Try different viewers (3D Slicer, Horos, OHIF)
