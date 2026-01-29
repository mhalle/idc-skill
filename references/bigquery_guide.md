# BigQuery Guide for IDC Data

This reference covers advanced access to IDC data via Google BigQuery for full DICOM metadata queries.

## When to Use BigQuery vs idc-index

| Use Case | idc-index | BigQuery |
|----------|-----------|----------|
| Quick series queries | ✓ Best | Works |
| Download DICOM files | ✓ Required | Cannot |
| Full DICOM metadata | Limited | ✓ Best |
| Clinical data joins | Limited | ✓ Best |
| Custom SQL analysis | DuckDB subset | ✓ Full SQL |
| No GCP account needed | ✓ Yes | Requires GCP |
| Cost | Free | Pay per query |

**Recommendation:** Start with idc-index for most tasks. Use BigQuery when you need:
- Full DICOM tag access beyond indexed columns
- Complex joins with clinical/genomic data
- Access to segmentation and measurement tables
- Analysis at scale with SQL

## Setup Requirements

### 1. GCP Account and Project

```bash
# Create a GCP account at https://cloud.google.com/
# Create a new project or use an existing one

# Enable the BigQuery API
gcloud services enable bigquery.googleapis.com
```

### 2. Authentication

```bash
# Install Google Cloud SDK if needed
# https://cloud.google.com/sdk/docs/install

# Authenticate for local development
gcloud auth application-default login

# Set your default project
gcloud config set project YOUR_PROJECT_ID
```

### 3. Python Dependencies

```python
# /// script
# dependencies = [
#   "google-cloud-bigquery",
#   "pandas",
#   "idc-index"
# ]
# ///
```

Or install with pip:
```bash
pip install google-cloud-bigquery pandas idc-index
```

## Dataset Architecture

IDC data is available in BigQuery under the `bigquery-public-data` project.

### Public Datasets

| Dataset | Description |
|---------|-------------|
| `bigquery-public-data.idc_current` | Latest IDC version (for exploration) |
| `bigquery-public-data.idc_current_clinical` | Clinical data for latest version |
| `bigquery-public-data.idc_v{N}` | Specific version (e.g., `idc_v23`) |
| `bigquery-public-data.idc_v{N}_clinical` | Clinical data for specific version |

**For reproducibility:** Always use versioned datasets (e.g., `idc_v23`) in published research.

### Key Tables

| Table | Description |
|-------|-------------|
| `dicom_all` | All DICOM metadata with IDC columns (collection_id, gcs_url, license) |
| `segmentations` | DICOM Segmentation objects |
| `measurement_groups` | SR TID1500 measurement groups |
| `quantitative_measurements` | Numeric measurements |
| `qualitative_measurements` | Coded evaluations |
| `original_collections_metadata` | Collection-level descriptions |

## Query Examples

### Basic: Find Series by Criteria

```python
from google.cloud import bigquery

client = bigquery.Client()

query = """
SELECT
    SeriesInstanceUID,
    Modality,
    BodyPartExamined,
    collection_id
FROM `bigquery-public-data.idc_current.dicom_all`
WHERE Modality = 'CT'
AND BodyPartExamined = 'CHEST'
GROUP BY SeriesInstanceUID, Modality, BodyPartExamined, collection_id
LIMIT 10
"""

df = client.query(query).to_dataframe()
print(df)
```

### Get GCS URLs for Download

```python
query = """
SELECT
    SeriesInstanceUID,
    gcs_url,
    collection_id
FROM `bigquery-public-data.idc_current.dicom_all`
WHERE collection_id = 'tcga_luad'
AND Modality = 'CT'
GROUP BY SeriesInstanceUID, gcs_url, collection_id
LIMIT 5
"""

df = client.query(query).to_dataframe()
# gcs_url points to individual DICOM files in gs://
```

### Access Full DICOM Tags

```python
# BigQuery stores DICOM tags that idc-index doesn't index
query = """
SELECT
    SeriesInstanceUID,
    SliceThickness,
    PixelSpacing,
    ImagePositionPatient,
    WindowCenter,
    WindowWidth,
    RescaleSlope,
    RescaleIntercept
FROM `bigquery-public-data.idc_current.dicom_all`
WHERE Modality = 'CT'
AND SliceThickness IS NOT NULL
GROUP BY 1,2,3,4,5,6,7,8
LIMIT 10
"""
```

### Join Clinical + Imaging Data

Clinical data is in the `idc_current_clinical` (or `idc_v{N}_clinical`) dataset with collection-specific tables.

```python
# First, list available clinical tables
tables_query = """
SELECT table_name
FROM `bigquery-public-data.idc_current_clinical.INFORMATION_SCHEMA.TABLES`
"""

# Then join with imaging data
query = """
SELECT
    d.SeriesInstanceUID,
    d.PatientID,
    d.Modality,
    c.age_at_diagnosis,
    c.pathologic_stage
FROM `bigquery-public-data.idc_current.dicom_all` d
JOIN `bigquery-public-data.idc_current_clinical.tcga_luad_clinical` c
    ON d.PatientID = c.dicom_patient_id
WHERE d.collection_id = 'tcga_luad'
AND d.Modality = 'CT'
GROUP BY 1,2,3,4,5
LIMIT 20
"""
```

**Note:** Clinical table schemas vary by collection. Check column names with `INFORMATION_SCHEMA.COLUMNS` before querying.

### Query Segmentations

```python
query = """
SELECT
    SeriesInstanceUID,
    SegmentLabel,
    SegmentAlgorithmName,
    SegmentedPropertyTypeCodeMeaning
FROM `bigquery-public-data.idc_current.segmentations`
WHERE SegmentedPropertyTypeCodeMeaning LIKE '%tumor%'
LIMIT 10
"""
```

## Cost Optimization

BigQuery charges by data scanned. Follow these practices to minimize costs:

### 1. Select Only Needed Columns

```sql
-- BAD: Scans entire table
SELECT * FROM `bigquery-public-data.idc_current.dicom_all` LIMIT 10

-- GOOD: Scans only selected columns
SELECT SeriesInstanceUID, Modality
FROM `bigquery-public-data.idc_current.dicom_all`
LIMIT 10
```

### 2. Filter Early with WHERE

```sql
-- Apply filters to reduce scanned data
SELECT SeriesInstanceUID, Modality
FROM `bigquery-public-data.idc_current.dicom_all`
WHERE collection_id = 'tcga_luad'  -- Filters early
AND Modality = 'CT'
LIMIT 10
```

### 3. Use Query Dry Run

```python
from google.cloud import bigquery

client = bigquery.Client()
job_config = bigquery.QueryJobConfig(dry_run=True)

query = "SELECT * FROM `bigquery-public-data.idc_current.dicom_all` LIMIT 10"
job = client.query(query, job_config=job_config)

# Estimate bytes before running
print(f"This query will process {job.total_bytes_processed / 1e9:.2f} GB")
```

### 4. Approximate Cost

- First 1 TB/month is free
- After that: ~$5 per TB scanned
- `dicom_all` is ~500 GB; full scan costs ~$2.50

## Combined Workflow: idc-index + BigQuery

Use idc-index for discovery, BigQuery for deep analysis:

```python
# /// script
# dependencies = [
#   "idc-index",
#   "google-cloud-bigquery",
#   "pandas"
# ]
# ///

from idc_index import IDCClient
from google.cloud import bigquery

# Step 1: Quick discovery with idc-index
idc = IDCClient()
series_df = idc.sql_query("""
    SELECT SeriesInstanceUID, collection_id, series_size_MB
    FROM index
    WHERE Modality = 'CT'
    AND BodyPartExamined = 'CHEST'
    AND series_size_MB < 100
    LIMIT 5
""")

# Step 2: Get detailed DICOM metadata from BigQuery
series_uids = series_df['SeriesInstanceUID'].tolist()
uid_list = ', '.join([f"'{uid}'" for uid in series_uids])

bq = bigquery.Client()
detailed_query = f"""
SELECT
    SeriesInstanceUID,
    SliceThickness,
    PixelSpacing,
    KVP,
    Exposure,
    ConvolutionKernel
FROM `bigquery-public-data.idc_current.dicom_all`
WHERE SeriesInstanceUID IN ({uid_list})
GROUP BY 1,2,3,4,5,6
"""

detailed_df = bq.query(detailed_query).to_dataframe()
print(detailed_df)

# Step 3: Download selected series with idc-index
idc.download_from_selection(
    seriesInstanceUID=series_uids[:2],
    downloadDir="./downloads"
)
```

## Resources

- [IDC BigQuery Documentation](https://learn.canceridc.dev/data/bigquery)
- [BigQuery SQL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax)
- [IDC Schema Explorer](https://learn.canceridc.dev/data/bigquery/idc-current-schema)
