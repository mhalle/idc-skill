# DICOMweb Access Guide

This reference covers accessing IDC data via DICOMweb APIs for PACS integration, streaming, and custom viewers.

## When to Use DICOMweb

| Use Case | Best Approach |
|----------|---------------|
| Bulk downloads | idc-index (faster) |
| PACS integration | DICOMweb |
| Custom viewer integration | DICOMweb |
| Streaming pixel data | DICOMweb |
| Metadata queries | idc-index or DICOMweb |
| Finding series UIDs | idc-index (recommended) |

**Key Point:** DICOMweb is read-only. Use it for retrieval, not storage.

## Endpoints

### Public Proxy (No Authentication)

IDC provides a public proxy for DICOMweb access:

```
https://proxy.imaging.datacommons.cancer.gov/current/viewer-only-no-downloads-see-tinyurl-dot-com-slash-3j3d9jyp/dicomWeb
```

**Notes:**
- Points to the latest IDC version automatically
- Daily quota applies (suitable for testing and moderate use)
- No authentication required
- The "viewer-only-no-downloads" in the URL is legacy naming with no functional meaning

### GCP Healthcare API (Authenticated)

For production use with higher quotas:

```
https://healthcare.googleapis.com/v1/projects/nci-idc-data/locations/us-central1/datasets/idc/dicomStores/idc-store-v{VERSION}/dicomWeb
```

**Requirements:**
- GCP account with `gcloud auth application-default login`
- Replace `{VERSION}` with IDC version number (e.g., `23` for v23)

To find the current version:
```python
from idc_index import IDCClient
client = IDCClient()
print(client.get_idc_version())  # e.g., "23"
```

## Supported Operations

IDC DICOMweb endpoints support standard DICOM Web Services:

| Operation | Method | Description |
|-----------|--------|-------------|
| QIDO-RS | GET | Query for studies/series/instances |
| WADO-RS | GET | Retrieve DICOM objects |
| STOW-RS | - | Not supported (read-only) |

### Searchable DICOM Tags (QIDO-RS)

The implementation supports a limited set of searchable tags:

| Level | Searchable Tags |
|-------|-----------------|
| Study | StudyInstanceUID, PatientName, PatientID, AccessionNumber, ReferringPhysicianName, StudyDate |
| Series | All study tags + SeriesInstanceUID, Modality |
| Instance | All series tags + SOPInstanceUID |

**Important:** Only exact matching is supported, except for StudyDate (range queries) and PatientName (fuzzy matching).

## QIDO-RS: Query Operations

### Query Studies

```python
import requests

base_url = "https://proxy.imaging.datacommons.cancer.gov/current/viewer-only-no-downloads-see-tinyurl-dot-com-slash-3j3d9jyp/dicomWeb"

# Query studies by patient ID
response = requests.get(
    f"{base_url}/studies",
    params={
        "PatientID": "TCGA-17-Z000",
        "limit": 10
    },
    headers={"Accept": "application/dicom+json"}
)

studies = response.json()
for study in studies:
    print(study.get("0020000D", {}).get("Value", [""])[0])  # StudyInstanceUID
```

### Query Series

```python
# Query series within a study
study_uid = "1.2.3.4.5.6.7.8.9"
response = requests.get(
    f"{base_url}/studies/{study_uid}/series",
    headers={"Accept": "application/dicom+json"}
)

series_list = response.json()
for series in series_list:
    modality = series.get("00080060", {}).get("Value", [""])[0]
    series_uid = series.get("0020000E", {}).get("Value", [""])[0]
    print(f"{modality}: {series_uid}")
```

### Query Instances

```python
# Query instances within a series
series_uid = "1.2.3.4.5.6.7.8.9.10"
response = requests.get(
    f"{base_url}/studies/{study_uid}/series/{series_uid}/instances",
    headers={"Accept": "application/dicom+json"}
)

instances = response.json()
print(f"Found {len(instances)} instances")
```

## WADO-RS: Retrieve Operations

### Retrieve DICOM Metadata

```python
# Get instance metadata (no pixel data)
instance_uid = "1.2.3.4.5.6.7.8.9.10.11"
response = requests.get(
    f"{base_url}/studies/{study_uid}/series/{series_uid}/instances/{instance_uid}/metadata",
    headers={"Accept": "application/dicom+json"}
)

metadata = response.json()
```

### Retrieve DICOM Instance

```python
# Get full DICOM file (with pixel data)
response = requests.get(
    f"{base_url}/studies/{study_uid}/series/{series_uid}/instances/{instance_uid}",
    headers={"Accept": "application/dicom"}
)

# Save as DICOM file
with open("instance.dcm", "wb") as f:
    f.write(response.content)
```

### Retrieve Rendered Image

```python
# Get rendered PNG/JPEG frame
response = requests.get(
    f"{base_url}/studies/{study_uid}/series/{series_uid}/instances/{instance_uid}/frames/1/rendered",
    headers={"Accept": "image/png"}
)

with open("frame.png", "wb") as f:
    f.write(response.content)
```

## Combined Workflow: idc-index + DICOMweb

Use idc-index to find UIDs, then DICOMweb for streaming:

```python
# /// script
# dependencies = [
#   "idc-index",
#   "requests"
# ]
# ///

from idc_index import IDCClient
import requests

# Step 1: Find series with idc-index (fast, indexed)
client = IDCClient()
df = client.sql_query("""
    SELECT SeriesInstanceUID, StudyInstanceUID,
           collection_id, Modality, series_size_MB
    FROM index
    WHERE Modality = 'CT'
    AND BodyPartExamined = 'CHEST'
    AND series_size_MB < 50
    LIMIT 1
""")

study_uid = df['StudyInstanceUID'].iloc[0]
series_uid = df['SeriesInstanceUID'].iloc[0]
print(f"Found series: {series_uid}")

# Step 2: Get instance list via DICOMweb
base_url = "https://proxy.imaging.datacommons.cancer.gov/current/viewer-only-no-downloads-see-tinyurl-dot-com-slash-3j3d9jyp/dicomWeb"

response = requests.get(
    f"{base_url}/studies/{study_uid}/series/{series_uid}/instances",
    headers={"Accept": "application/dicom+json"}
)

instances = response.json()
print(f"Series has {len(instances)} instances")

# Step 3: Stream first instance metadata
if instances:
    instance_uid = instances[0].get("00080018", {}).get("Value", [""])[0]

    meta_response = requests.get(
        f"{base_url}/studies/{study_uid}/series/{series_uid}/instances/{instance_uid}/metadata",
        headers={"Accept": "application/dicom+json"}
    )

    metadata = meta_response.json()
    print(f"Instance SOP Class: {metadata[0].get('00080016', {}).get('Value', [''])[0]}")
```

## Authentication for GCP Healthcare API

For full access via GCP Healthcare API:

```python
from google.auth import default
from google.auth.transport.requests import Request
import requests

# Get credentials
credentials, project = default(scopes=['https://www.googleapis.com/auth/cloud-healthcare'])
credentials.refresh(Request())

# Make authenticated request (replace 23 with current IDC version)
base_url = "https://healthcare.googleapis.com/v1/projects/nci-idc-data/locations/us-central1/datasets/idc/dicomStores/idc-store-v23/dicomWeb"

response = requests.get(
    f"{base_url}/studies",
    params={"limit": 5},
    headers={
        "Authorization": f"Bearer {credentials.token}",
        "Accept": "application/dicom+json"
    }
)

print(response.json())
```

## Query Parameters

Common QIDO-RS query parameters:

| Parameter | Example | Description |
|-----------|---------|-------------|
| `PatientID` | `TCGA-AA-0001` | Exact patient ID |
| `StudyDate` | `20200101-20201231` | Date range |
| `Modality` | `CT` | DICOM modality |
| `limit` | `100` | Max results |
| `offset` | `50` | Skip results (pagination) |

## Troubleshooting

### 400 Bad Request on search queries

- **Cause:** Using unsupported search parameters
- **Solution:** Use UID-based queries. For filtering by Modality or other attributes, use idc-index to discover UIDs first

### 403 Forbidden

- Public proxy may be rate limiting
- For GCP API: run `gcloud auth application-default login`

### 429 Too Many Requests

- **Cause:** Rate limit exceeded
- **Solution:** Add delays between requests, reduce `limit` values, or use authenticated endpoint

### 204 No Content for valid UIDs

- **Cause:** UID may be from an older IDC version
- **Solution:** Verify UID exists using idc-index query first

### Empty Results

- Verify UIDs are correct (use idc-index to validate)
- Check DICOM tag format (query uses DICOM tags, not column names)

### Slow Responses

- Use idc-index for initial queries
- DICOMweb is optimized for retrieval, not large-scale queries

### CORS Issues (Browser)

- Public proxy includes CORS headers
- For custom domains, use server-side proxy

## Resources

- [DICOMweb Standard](https://www.dicomstandard.org/using/dicomweb)
- [IDC DICOMweb Documentation](https://learn.canceridc.dev/data/dicomweb)
- [GCP Healthcare API](https://cloud.google.com/healthcare-api/docs/dicom)
