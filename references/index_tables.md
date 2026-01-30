# Index Tables Reference

This reference documents all available index tables in idc-index and how to use them.

## Available Tables

| Table | Row Granularity | Loaded | Description |
|-------|-----------------|--------|-------------|
| `index` | 1 row = 1 DICOM series | Auto | Primary metadata for all current IDC data |
| `prior_versions_index` | 1 row = 1 DICOM series | Auto | Series from previous IDC releases |
| `collections_index` | 1 row = 1 collection | fetch_index() | Collection-level metadata and descriptions |
| `analysis_results_index` | 1 row = 1 analysis result | fetch_index() | Metadata about derived datasets |
| `clinical_index` | 1 row = 1 clinical column | fetch_index() | Dictionary mapping clinical columns to collections |
| `sm_index` | 1 row = 1 slide microscopy series | fetch_index() | Slide microscopy (pathology) metadata |
| `sm_instance_index` | 1 row = 1 slide microscopy instance | fetch_index() | Instance-level slide microscopy metadata |
| `seg_index` | 1 row = 1 DICOM Segmentation series | fetch_index() | Segmentation metadata with algorithm info |

**Auto** = loaded when `IDCClient()` is instantiated
**fetch_index()** = requires `client.fetch_index("table_name")` to load

## Accessing Tables

### Via SQL (recommended)

```python
from idc_index import IDCClient
client = IDCClient()

# Query primary index (always available)
results = client.sql_query("SELECT * FROM index WHERE Modality = 'CT' LIMIT 10")

# Fetch and query additional indices
client.fetch_index("collections_index")
collections = client.sql_query("SELECT collection_id, CancerTypes FROM collections_index")

client.fetch_index("seg_index")
segs = client.sql_query("SELECT * FROM seg_index LIMIT 5")
```

### As DataFrames

```python
# Primary index
df = client.index

# After fetching
client.fetch_index("sm_index")
sm_df = client.sm_index
```

## Schema Discovery with indices_overview

Use `client.indices_overview` as the authoritative source for column schemas:

```python
from idc_index import IDCClient
client = IDCClient()

# List all indices with descriptions
for name, info in client.indices_overview.items():
    print(f"{name}: {info['description']}")
    print(f"  Installed: {info['installed']}")

# Get complete schema for a table
schema = client.indices_overview["index"]["schema"]
print(f"Table: {schema['table_description']}")

for col in schema['columns']:
    print(f"  {col['name']} ({col['type']}): {col.get('description', '')}")
```

Alternative method:
```python
schema = client.get_index_schema("index")
```

## Join Columns

| Join Column | Tables | Use Case |
|-------------|--------|----------|
| `collection_id` | index, collections_index, clinical_index | Link series to collection metadata |
| `SeriesInstanceUID` | index, sm_index, seg_index | Link series across tables |
| `StudyInstanceUID` | index, prior_versions_index | Link studies across versions |
| `PatientID` | index, prior_versions_index | Link patients across versions |
| `analysis_result_id` | index, analysis_results_index | Link to analysis metadata |
| `segmented_SeriesInstanceUID` | seg_index → index | Link segmentation to source image |

## Example Joins

### Join with collections_index for cancer types

```python
client.fetch_index("collections_index")
result = client.sql_query("""
    SELECT i.SeriesInstanceUID, i.Modality, c.CancerTypes, c.TumorLocations
    FROM index i
    JOIN collections_index c ON i.collection_id = c.collection_id
    WHERE i.Modality = 'MR'
    LIMIT 10
""")
```

### Join with sm_index for slide microscopy details

```python
client.fetch_index("sm_index")
result = client.sql_query("""
    SELECT i.collection_id, i.PatientID, s.ObjectiveLensPower, s.min_PixelSpacing_2sf
    FROM index i
    JOIN sm_index s ON i.SeriesInstanceUID = s.SeriesInstanceUID
    LIMIT 10
""")
```

### Join seg_index to find segmentations with source images

```python
client.fetch_index("seg_index")
result = client.sql_query("""
    SELECT
        s.SeriesInstanceUID as seg_series,
        s.AlgorithmName,
        s.total_segments,
        src.collection_id,
        src.Modality as source_modality
    FROM seg_index s
    JOIN index src ON s.segmented_SeriesInstanceUID = src.SeriesInstanceUID
    WHERE s.AlgorithmType = 'AUTOMATIC'
    LIMIT 10
""")
```

### Find analysis results for a collection

```python
client.fetch_index("analysis_results_index")
result = client.sql_query("""
    SELECT analysis_result_id, analysis_result_title, Modalities
    FROM analysis_results_index
    WHERE Collections LIKE '%tcga_luad%'
""")
```

## Key Columns in Primary Index

Most common columns (use `indices_overview` for complete list):

| Column | Type | DICOM | Description |
|--------|------|-------|-------------|
| `collection_id` | STRING | No | IDC collection identifier |
| `analysis_result_id` | STRING | No | Analysis results collection (if applicable) |
| `PatientID` | STRING | Yes | Patient identifier |
| `StudyInstanceUID` | STRING | Yes | DICOM Study UID |
| `SeriesInstanceUID` | STRING | Yes | DICOM Series UID (use for downloads) |
| `Modality` | STRING | Yes | Imaging modality (CT, MR, PT, SM, etc.) |
| `BodyPartExamined` | STRING | Yes | Anatomical region |
| `SeriesDescription` | STRING | Yes | Description of the series |
| `Manufacturer` | STRING | Yes | Equipment manufacturer |
| `license_short_name` | STRING | No | License type (CC BY 4.0, etc.) |
| `series_size_MB` | FLOAT | No | Size in megabytes |
| `instanceCount` | INTEGER | No | Number of DICOM instances |

**DICOM = Yes**: Value extracted from DICOM attribute with same name.

## Clinical Data Access

Clinical data is available for select collections. Not all collections have clinical data.

### Discovering Available Clinical Data

```python
# Fetch clinical index (downloads clinical tables)
client.fetch_index("clinical_index")

# List collections with clinical data
collections_with_clinical = client.sql_query("""
    SELECT DISTINCT collection_id, COUNT(DISTINCT table_name) as tables
    FROM clinical_index
    GROUP BY collection_id
    ORDER BY tables DESC
""")

# Find tables and columns for a specific collection
tcga_tables = client.sql_query("""
    SELECT table_name, column_label, column_description
    FROM clinical_index
    WHERE collection_id = 'tcga_luad'
    ORDER BY table_name, column_label
""")
```

### Loading Clinical Tables

```python
# Load a specific clinical table as DataFrame
clinical_df = client.get_clinical_table("tcga_luad_clinical")

# Common clinical table naming patterns:
# - {collection}_clinical (main clinical data)
# - {collection}_biospecimen (sample info)
# - {collection}_followup (longitudinal data)
```

### Joining Clinical with Imaging Data

```python
# Method 1: Filter imaging by patients with clinical data
result = client.sql_query("""
    SELECT i.PatientID, i.SeriesInstanceUID, i.Modality, i.SeriesDescription
    FROM index i
    WHERE i.collection_id = 'tcga_luad'
    AND i.PatientID IN (
        SELECT DISTINCT dicom_patient_id FROM tcga_luad_clinical
    )
    LIMIT 20
""")

# Method 2: Load both and merge in pandas
import pandas as pd

imaging_df = client.sql_query("""
    SELECT PatientID, SeriesInstanceUID, Modality
    FROM index WHERE collection_id = 'tcga_luad'
""")
clinical_df = client.get_clinical_table("tcga_luad_clinical")

# Clinical tables use 'dicom_patient_id' to match 'PatientID'
merged = imaging_df.merge(
    clinical_df,
    left_on='PatientID',
    right_on='dicom_patient_id'
)
```

### Common Clinical Columns

Clinical table schemas vary by collection. Check column names with:

```python
# Get all columns for a collection's clinical data
cols = client.sql_query("""
    SELECT column_label, column_description
    FROM clinical_index
    WHERE table_name = 'tcga_luad_clinical'
""")
```

Common columns include:
- `dicom_patient_id` - Links to imaging PatientID
- `age_at_diagnosis` - Patient age
- `gender` or `sex` - Patient sex
- `pathologic_stage` - Cancer staging
- `vital_status` - Alive/deceased
- `days_to_death` or `days_to_last_followup` - Survival data

### BigQuery Clinical Data

For more complex clinical queries, BigQuery provides direct access:

```sql
-- BigQuery: Join imaging with clinical
SELECT
    d.PatientID,
    d.SeriesInstanceUID,
    d.Modality,
    c.age_at_diagnosis,
    c.pathologic_stage
FROM `bigquery-public-data.idc_current.dicom_all` d
JOIN `bigquery-public-data.idc_current_clinical.tcga_luad_clinical` c
    ON d.PatientID = c.dicom_patient_id
WHERE d.collection_id = 'tcga_luad'
    AND d.Modality = 'CT'
LIMIT 20
```

**Note:** BigQuery clinical tables are in `idc_current_clinical` dataset.
