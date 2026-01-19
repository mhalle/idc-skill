---
name: idc-skill
description: This skill should be used when exploring cancer imaging data from the Imaging Data Commons (IDC). Use when querying medical imaging metadata, searching for DICOM series, analyzing imaging collections, or preparing datasets for download. Triggers include queries about CT/MR/PET scans, cancer imaging studies, DICOM data, or IDC collections.
metadata:
  version: 0.1.0
  repository: https://github.com/mhalle/idc-skill
---

# IDC Data Exploration

## Overview

This skill enables exploration and analysis of cancer imaging data from the Imaging Data Commons (IDC) using the idc-index Python package. The skill handles querying 965,407 DICOM series across 161 collections, identifying relevant datasets, and managing workflows for both restricted (LLM built-in) and unrestricted (Claude Code, local) environments.

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

### Initial Setup

Install and initialize the IDC client:

```python
# Install uv for package management
pip install uv --break-system-packages

# For scripts, use PEP723 inline dependency specifications
# /// script
# dependencies = [
#   "idc-index==0.10.2",
#   "pydicom"
# ]
# ///
```

Verify version compatibility:

```python
import importlib.metadata
from idc_index import IDCClient

installed_version = importlib.metadata.version('idc-index')
print(f"Installed: {installed_version}")
# Documented version: 0.10.2

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
- 965,407 series across 161 collections
- Two SQL-queryable tables: `index` (current data) and `prior_versions_index` (historical)
- Key columns: SeriesInstanceUID (primary key), Modality, BodyPartExamined, series_size_MB

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
# dependencies = [
#   "idc-index==0.10.2",
# ]
# ///

from idc_index import IDCClient
import zipfile
from pathlib import Path

# Series UIDs from query
series_uids = [
    "1.2.276.0.7230010.3.1.4.8323329.5323.1517875193.899377",
    # ... additional UIDs
]

client = IDCClient()
download_dir = Path("idc_downloads")
download_dir.mkdir(exist_ok=True)

# Download each series
for uid in series_uids:
    print(f"Downloading {uid}...")
    client.download_dicom_series(
        uid, 
        downloadDir=str(download_dir),
        show_progress_bar=True,
        quiet=False
    )

# Create zip file
output_zip = "idc_data.zip"
with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file_path in download_dir.rglob('*'):
        if file_path.is_file():
            zipf.write(file_path, file_path.relative_to(download_dir.parent))

print(f"Created {output_zip}")
```

**Step 3: User execution and upload**
- User saves script and runs in unrestricted environment
- Script downloads DICOM files and creates zip
- User uploads zip file
- Extract and analyze: `unzip idc_data.zip -d /home/claude/dicom_data/`

### Workflow 3: Direct Download (Unrestricted Environment)

When operating in an unrestricted environment, download directly:

```python
from idc_index import IDCClient

client = IDCClient()

# Download series directly
client.download_dicom_series(
    "1.2.276.0.7230010.3.1.4.8323329.5323.1517875193.899377",
    downloadDir="/home/claude/downloads",
    show_progress_bar=True
)

# Fetch additional indices
client.fetch_index('clinical_index')
clinical_data = client.get_clinical_table('tcga_luad')

# Analyze immediately
import pydicom
dcm = pydicom.dcmread('/home/claude/downloads/file.dcm')
print(dcm.PatientID, dcm.StudyDate)
```

### Workflow 4: Analyze DICOM Files

After obtaining DICOM files (via either workflow), analyze with pydicom:

```python
import pydicom
from pathlib import Path

# Read DICOM file
dcm = pydicom.dcmread('path/to/file.dcm')

# Access metadata
print(f"Patient ID: {dcm.PatientID}")
print(f"Modality: {dcm.Modality}")
print(f"Study Date: {dcm.StudyDate}")

# Access pixel data (if available)
if hasattr(dcm, 'pixel_array'):
    pixels = dcm.pixel_array
    print(f"Image shape: {pixels.shape}")
```

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

In unrestricted environments, fetch optional indices:

```python
# Slide Microscopy series index
client.fetch_index('sm_index')
# Access: client.sm_index

# Slide Microscopy instance-level index
client.fetch_index('sm_instance_index')
# Access: client.sm_instance_index

# Clinical data index
client.fetch_index('clinical_index')
# Access: client.clinical_index
# Get collection data: client.get_clinical_table('collection_id')
```

**Note:** These operations fail in restricted environments with 403 or S3 errors.

## Best Practices

1. **Detect environment early** - Try a simple operation to determine restrictions
2. **Verify version compatibility** - Check installed version matches 0.10.2
3. **Start with small queries** - Use `LIMIT 10` to understand data structure
4. **Check series_size_MB** - Prefer <100MB for testing, <30MB for quick downloads
5. **Inspect null counts** - Many clinical fields have significant nulls (see schema reference)
6. **Use citations** - Always cite data sources: `client.citations_from_selection()`
7. **Verify licenses** - Check `license_short_name` column before use
8. **Mind large collections** - NLST has 587,799 series (60% of all data)
9. **Generate scripts thoughtfully** - In restricted environments, create clear, documented scripts for users

## Common Issues

**Issue:** Network operations fail (403 errors, s5cmd failures)
- **Solution:** Recognize restricted environment, use three-step workflow

**Issue:** SQL query fails
- **Solution:** Verify table name is `index` or `prior_versions_index`, check DuckDB syntax

**Issue:** Need clinical data but fetch_index fails
- **Solution:** In restricted environment, inform user that clinical data requires unrestricted environment

**Issue:** Large result sets overwhelming
- **Solution:** Add LIMIT clauses, filter by series_size_MB, use aggregations first

**Issue:** Can't find specific imaging modality
- **Solution:** Check `references/schema_reference.md` for modality codes (SR, CT, SEG, MR, etc.)

## Resources

### references/

- `schema_reference.md` - Complete schema documentation for both index tables
- `query_patterns.md` - Comprehensive SQL query examples for common tasks

Load these references when detailed information is needed for schema understanding or query construction.
