---
name: idc-skill
description: This skill should be used when exploring cancer imaging data from the Imaging Data Commons (IDC). Use when the user explicitly mentions IDC, Imaging Data Commons, or IDC collections. Do not trigger on general medical imaging queries unless IDC is specifically referenced.
metadata:
  version: 0.3.1
  repository: https://github.com/mhalle/idc-skill
---

# IDC Data Exploration

## Overview

This skill enables exploration and analysis of cancer imaging data from the Imaging Data Commons (IDC) using the idc-index Python package. IDC contains hundreds of thousands of DICOM series across 160+ collections—query for current stats:

```python
from idc_index import IDCClient
client = IDCClient()
stats = client.sql_query("""
    SELECT COUNT(DISTINCT collection_id) as collections,
           COUNT(*) as series,
           ROUND(SUM(series_size_MB)/1000, 1) as total_GB
    FROM index
""")
```

The skill handles identifying relevant datasets and managing workflows for both restricted (LLM built-in) and unrestricted (Claude Code, local) environments.

## Data Access Methods

| Method | Auth Required | Best For | Cost |
|--------|---------------|----------|------|
| **idc-index** | No | Queries, downloads, most tasks | Free |
| **IDC Portal** | No | Interactive exploration | Free |
| **Viewers (OHIF/SLIM)** | No | Quick visualization | Free |
| **DICOMweb** | No (proxy) | PACS integration, streaming | Free |
| **BigQuery** | Yes (GCP) | Full DICOM metadata, complex joins | Pay per query |

**Default choice:** Use `idc-index` for most tasks. It requires no authentication, handles downloads efficiently, and covers the vast majority of use cases. Only consider BigQuery or DICOMweb for specialized needs not met by idc-index.

## IDC Data Model

IDC adds grouping levels above the standard DICOM hierarchy:

```
collection_id → PatientID → StudyInstanceUID → SeriesInstanceUID → SOPInstanceUID
```

| Identifier | Scope | Use For |
|------------|-------|---------|
| `collection_id` | Dataset grouping | Filtering by project/disease |
| `analysis_result_id` | Derived data grouping | Finding segmentations/annotations |
| `PatientID` | Patient | Grouping images by subject |
| `StudyInstanceUID` | DICOM study | Visualization, grouping series |
| `SeriesInstanceUID` | DICOM series | Downloads, queries |

- **collection_id**: Groups patients by disease, modality, or research focus (e.g., `tcga_luad`, `nlst`)
- **analysis_result_id**: Identifies derived objects (segmentations, annotations) across collections

See `references/index_tables.md` for complete table documentation and join patterns.

## Environment Detection

Detect the operating environment early to choose the appropriate workflow:

**Restricted Environment Indicators:**
- 403 errors when calling `client.fetch_index()`
- S5 command failures (s5cmd errors)
- Network timeout errors on data operations
- LLM built-in Linux (Claude web interface, similar environments)

**Unrestricted Environment Indicators:**
- Claude Code
- User's local machine
- Successful `client.fetch_index()` calls
- Successful `client.download_dicom_*()` calls

**Important:** Python package installation via `pip` or `uv` may succeed in restricted environments even when other network operations fail.

## Quick Start

### Running Scripts with uv (Recommended)

Use `uv run` with PEP723 inline dependency specifications. This automatically handles package installation without polluting the global environment.

First, ensure uv is installed:
```bash
pip install uv --break-system-packages
```

Then create scripts with inline dependencies:
```python
# /// script
# dependencies = [
#   "idc-index",
#   "pydicom"
# ]
# ///

from idc_index import IDCClient

client = IDCClient()
# ... your code here
```

Run the script with:
```bash
uv run script.py
```

### Fallback: Install with pip

If uv is not available, install packages directly:
```bash
pip install idc-index pydicom --break-system-packages
```

Then run Python normally:
```python
from idc_index import IDCClient

client = IDCClient()
```

### Basic Query Pattern

Query the main index using DuckDB SQL:

```python
# Find CT scans of chest under 100MB
df = client.sql_query("""
    SELECT SeriesInstanceUID, series_size_MB, 
           collection_id, PatientID
    FROM index 
    WHERE Modality = 'CT' 
    AND BodyPartExamined LIKE '%CHEST%'
    AND series_size_MB < 100
    LIMIT 10
""")
```

## Core Workflows

### Workflow 1: Query and Explore (Both Environments)

Use SQL queries to find relevant imaging data:

**Step 1: Understand the dataset structure**
- Two SQL-queryable tables: `index` (current data) and `prior_versions_index` (historical)
- Key columns: SeriesInstanceUID (primary key), Modality, BodyPartExamined, series_size_MB
- Use `client.get_idc_version()` to check data version

**Step 2: Query for specific criteria**

```python
# Find all brain MR scans under 50MB
df = client.sql_query("""
    SELECT SeriesInstanceUID, series_size_MB, 
           collection_id, Modality, BodyPartExamined
    FROM index 
    WHERE Modality = 'MR' 
    AND BodyPartExamined = 'BRAIN'
    AND series_size_MB < 50
    ORDER BY series_size_MB ASC
""")
```

**Step 3: Analyze collections**

```python
# Get series count and size by modality for a collection
df = client.sql_query("""
    SELECT Modality, 
           COUNT(*) as series_count,
           SUM(series_size_MB) as total_mb,
           AVG(series_size_MB) as avg_mb
    FROM index
    WHERE collection_id = 'tcga_luad'
    GROUP BY Modality
    ORDER BY series_count DESC
""")
```

### Workflow 2: Download Data (Restricted Environment)

When operating in a restricted environment, use the three-step process:

**Step 1: Query and collect SeriesInstanceUIDs**

```python
# Find interesting series
df = client.sql_query("""
    SELECT SeriesInstanceUID, series_size_MB, 
           collection_id, Modality
    FROM index 
    WHERE Modality = 'MR'
    AND series_size_MB < 30
    LIMIT 5
""")

series_uids = df['SeriesInstanceUID'].tolist()
```

**Step 2: Generate download script for user**

Create a standalone Python script with PEP723 dependencies:

```python
# /// script
# dependencies = ["idc-index"]
# ///
from idc_index import IDCClient

series_uids = ["1.2.276...", "1.2.277..."]  # UIDs from query

client = IDCClient()
client.download_from_selection(
    seriesInstanceUID=series_uids,
    downloadDir="./idc_downloads"
)
print("Download complete")
```

**Step 3: User execution and upload**
- User saves script and runs with `uv run script.py`
- User uploads downloaded files or zips them first

### Workflow 3: Direct Download (Unrestricted Environment)

When operating in an unrestricted environment, download directly:

```python
from idc_index import IDCClient

client = IDCClient()

# Download specific series
client.download_from_selection(
    seriesInstanceUID=["1.2.276.0.7230010.3.1.4.8323329.5323.1517875193.899377"],
    downloadDir="./downloads"
)

# Download entire collection
client.download_from_selection(
    collection_id="rider_pilot",
    downloadDir="./data/rider"
)

# Custom directory structure
client.download_from_selection(
    collection_id="tcga_luad",
    downloadDir="./data",
    dirTemplate="%collection_id/%PatientID/%Modality"
)
```

See `references/downloads.md` for CLI commands, manifest files, and batch downloads.

### Workflow 4: Analyze DICOM Files

After obtaining DICOM files, analyze with pydicom or SimpleITK:

```python
import pydicom

dcm = pydicom.dcmread('path/to/file.dcm')
print(f"Patient: {dcm.PatientID}, Modality: {dcm.Modality}")

if hasattr(dcm, 'pixel_array'):
    pixels = dcm.pixel_array
```

```python
import SimpleITK as sitk

reader = sitk.ImageSeriesReader()
reader.SetFileNames(reader.GetGDCMSeriesFileNames("./ct_series"))
image = reader.Execute()
sitk.WriteImage(image, "volume.nii.gz")
```

See `references/analysis_pipelines.md` for 3D volume construction, radiomics, and pathology workflows.

### Workflow 5: Visualize in Browser

Preview imaging data without downloading using OHIF and SLIM viewers:

```python
from idc_index import IDCClient
import webbrowser

client = IDCClient()

# Find series to visualize
df = client.sql_query("""
    SELECT SeriesInstanceUID, StudyInstanceUID, Modality,
           collection_id, BodyPartExamined
    FROM index
    WHERE Modality = 'CT'
    AND BodyPartExamined = 'CHEST'
    LIMIT 3
""")

# Generate viewer URLs using get_viewer_URL() (auto-selects OHIF or SLIM)
for _, row in df.iterrows():
    viewer_url = client.get_viewer_URL(seriesInstanceUID=row['SeriesInstanceUID'])
    print(f"Collection: {row['collection_id']}")
    print(f"  {viewer_url}")
    # webbrowser.open(viewer_url)  # Uncomment to open
```

The `get_viewer_URL()` method automatically selects the appropriate viewer:
- **OHIF Viewer** for radiology (CT, MR, PET, X-ray)
- **SLIM Viewer** for slide microscopy (SM)

See `references/viewers_guide.md` for detailed viewer usage.

## Common Query Patterns

Reference the `references/query_patterns.md` file for comprehensive SQL query examples including:
- Finding specific modalities and body parts
- Date range filtering
- Aggregations by collection, modality, manufacturer
- Joining current and historical data
- Finding small series for quick analysis

## Dataset Schema

Reference the `references/schema_reference.md` file for detailed information on:
- Table structures (`index`, `prior_versions_index`)
- Column descriptions and data types
- Null value counts
- Modality codes and their meanings
- Collection statistics

## Additional Indices

Beyond the auto-loaded `index` and `prior_versions_index`, fetch optional indices as needed:

```python
client.fetch_index('collections_index')   # Collection metadata
client.fetch_index('analysis_results_index')  # Derived datasets
client.fetch_index('seg_index')           # Segmentation details
client.fetch_index('sm_index')            # Slide microscopy
client.fetch_index('clinical_index')      # Clinical data
```

Use `client.indices_overview` for authoritative schema information.

**Note:** Fetch operations fail in restricted environments with 403 or S3 errors.

### Clinical Data Access

```python
client.fetch_index("clinical_index")

# Load clinical table (naming: {collection}_clinical)
clinical_df = client.get_clinical_table("tcga_luad_clinical")

# Join with imaging via dicom_patient_id column
```

See `references/index_tables.md` for clinical table discovery, join patterns, and BigQuery examples.

## Advanced: BigQuery Access

**Important:** BigQuery is an advanced technique. Try `idc-index` queries first—they cover most use cases without authentication or cost.

### When BigQuery May Be Needed

Only consider BigQuery when `idc-index` cannot provide the data you need:
- Full DICOM metadata (all 4000+ tags vs ~50 in idc-index)
- Complex joins with clinical data tables
- DICOM sequence attributes (nested structures)
- Fields not available in the idc-index mini-index

### Requirements and Costs

| Requirement | Details |
|-------------|---------|
| GCP Account | Required with billing enabled |
| Authentication | `gcloud auth application-default login` |
| Cost | First 1 TB/month free, then ~$5/TB scanned |

### Quick Reference

```python
# Requires: pip install google-cloud-bigquery
# Auth: gcloud auth application-default login
from google.cloud import bigquery

client = bigquery.Client(project="your-gcp-project-id")

query = """
SELECT SeriesInstanceUID, SliceThickness, PixelSpacing
FROM `bigquery-public-data.idc_current.dicom_all`
WHERE collection_id = 'tcga_luad' AND Modality = 'CT'
LIMIT 10
"""
df = client.query(query).to_dataframe()
```

**Key datasets:**
- `bigquery-public-data.idc_current.*` - Latest version
- `bigquery-public-data.idc_v{N}.*` - Versioned (for reproducibility)
- `bigquery-public-data.idc_current_clinical.*` - Clinical data

See `references/bigquery_guide.md` for detailed setup, query patterns, and cost optimization.

## Collections Database

The skill includes a pre-built SQLite database of IDC collection metadata at `assets/idc_collections.db`. Use this for fast local lookups of collection information without API calls.

### Quick Lookup

```sql
-- Find collections by cancer type
SELECT collection_id, cancer_type, subject_count
FROM collections
WHERE cancer_type LIKE '%Lung%';

-- Full-text search across all fields
SELECT collection_id, cancer_type, location
FROM collections_fts
WHERE collections_fts MATCH 'breast screening';
```

### When to Use

**Always check the collections database first** before loading the `idc-index` module. The collections database is lightweight and fast, while `idc-index` is a large module that takes time to load.

- **Use the collections database** for:
  - Browsing available collections
  - Searching by cancer type, location, or keywords
  - Getting collection descriptions and metadata
  - Answering questions about what data IDC contains

- **Use `idc-index`** only when you need:
  - Series-level queries (individual DICOM series)
  - Downloading DICOM data
  - Access to the full imaging index

See `references/collections_database.md` for complete schema and query examples.

## Best Practices

1. **Detect environment early** - Try a simple operation to determine restrictions
2. **Use latest idc-index** - Keep the package updated (`pip install --upgrade idc-index`)
3. **Start with small queries** - Use `LIMIT 10` to understand data structure
4. **Check series_size_MB** - Prefer <100MB for testing, <30MB for quick downloads
5. **Use citations** - Generate with `client.citations_from_selection()` (see `references/licenses_citations.md`)
6. **Verify licenses** - Check `license_short_name` column before use
7. **Generate scripts thoughtfully** - In restricted environments, create clear scripts for users
8. **Use viewers for quick preview** - Generate OHIF/SLIM URLs before downloading

## Common Issues

- **403/s5cmd errors**: Restricted environment - use three-step workflow
- **SQL query fails**: Verify table name is `index` or `prior_versions_index`, check DuckDB syntax
- **fetch_index fails**: In restricted environment, clinical data requires unrestricted access
- **Large result sets**: Add LIMIT clauses, filter by series_size_MB, use aggregations
- **Can't find modality**: Check `references/schema_reference.md` for modality codes

## Checking for Updates

This skill's version is in the frontmatter metadata (`metadata.version`). To check for updates, compare against the latest GitHub release tag from `https://api.github.com/repos/mhalle/idc-skill/releases/latest`.

If outdated, offer to download the latest `.skill` file and present it to the user as an output file for reinstallation.

**Note:** This update workflow is Claude-specific. Other agents may use different conventions.

See `references/updating.md` for detailed update procedures.

## Resources

### references/

- `schema_reference.md` - Complete schema documentation for both index tables
- `query_patterns.md` - Comprehensive SQL query examples for common tasks
- `collections_database.md` - Schema and queries for the local collections database
- `updating.md` - Instructions for checking and applying skill updates
- `index_tables.md` - All 8 index tables, join patterns, and schema discovery
- `downloads.md` - Download API, CLI commands, templates, and manifests
- `licenses_citations.md` - License types, queries, and citation generation
- `segmentations.md` - Finding and using segmentations and annotations
- `analysis_pipelines.md` - Integration with pydicom, SimpleITK, and analysis workflows
- `bigquery_guide.md` - Advanced BigQuery access for full DICOM metadata
- `dicomweb_guide.md` - DICOMweb API access for PACS integration and streaming
- `viewers_guide.md` - Browser-based visualization with OHIF and SLIM viewers

### assets/

- `idc_collections.db` - Pre-built SQLite database of IDC collection metadata

Load these references when detailed information is needed for schema understanding or query construction.
