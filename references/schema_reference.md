# IDC Schema Reference

This reference provides complete documentation of the IDC index tables, columns, data types, and statistics.

## Table Overview

### `index` Table (Main Index)
- **Rows**: 965,407
- **Description**: One row per DICOM series in current IDC version (v22)
- **Primary Key**: SeriesInstanceUID

### `prior_versions_index` Table (Historical Data)
- **Rows**: 56,408
- **Description**: Series from previous IDC versions not in current version
- **Primary Key**: SeriesInstanceUID
- **Note**: 82% is Slide Microscopy (SM) data

## Complete Schema: `index` Table

### Identifier Columns

| Column | Type | Unique Values | Nulls | Description |
|--------|------|---------------|-------|-------------|
| collection_id | object | 161 | 0 | Thematic grouping identifier |
| PatientID | object | 79,214 | 0 | Patient/subject identifier |
| StudyInstanceUID | object | 159,593 | 0 | Unique identifier for imaging study |
| SeriesInstanceUID | object | 965,407 | 0 | **PRIMARY KEY** - Unique series identifier |
| crdc_series_uuid | object | 965,407 | 0 | Alternative series identifier |
| analysis_result_id | object | 11 | 552,087 | Links to derived/analysis results |

### Clinical/Demographic Columns

| Column | Type | Unique Values | Nulls | Description |
|--------|------|---------------|-------|-------------|
| PatientAge | object | 916 | 773,451 | Age at study time (format: '057Y') |
| PatientSex | object | 6 | 668,572 | Biological sex ('F', 'M', etc.) |
| StudyDate | object | 10,371 | 0 | Date of study (format: 'YYYY-MM-DD') |
| StudyDescription | object | 3,462 | 30,828 | Description of imaging study |

### Imaging Metadata Columns

| Column | Type | Unique Values | Nulls | Description |
|--------|------|---------------|-------|-------------|
| BodyPartExamined | object | 71 | 426,872 | Anatomical region imaged |
| Modality | object | 26 | 0 | Imaging modality (CT, MR, PT, etc.) |
| Manufacturer | object | 114 | 12,814 | Equipment manufacturer |
| ManufacturerModelName | object | 376 | 23,847 | Specific scanner model |
| SeriesDate | object | 10,264 | 287,330 | Series acquisition date |
| SeriesDescription | object | 92,552 | 48,515 | Detailed series description |
| SeriesNumber | object | 36,932 | 11,630 | Series number within study |
| instanceCount | Int64 | 1,011 | 0 | Number of DICOM files in series |

### Data Access Columns

| Column | Type | Unique Values | Nulls | Description |
|--------|------|---------------|-------|-------------|
| source_DOI | object | 215 | 0 | Digital Object Identifier for data |
| license_short_name | object | 5 | 0 | Data usage license (e.g., 'CC BY 3.0') |
| aws_bucket | object | 3 | 0 | S3 bucket name (e.g., 'idc-open-data') |
| series_aws_url | object | 965,407 | 0 | S3 URL for series data |
| series_size_MB | float64 | 65,202 | 0 | Total series size in megabytes |

## Complete Schema: `prior_versions_index` Table

| Column | Type | Description |
|--------|------|-------------|
| collection_id | object | Thematic grouping identifier |
| PatientID | object | Patient/subject identifier |
| SeriesInstanceUID | object | **PRIMARY KEY** - Unique series identifier |
| StudyInstanceUID | object | Unique identifier for imaging study |
| Modality | object | Imaging modality |
| gcs_bucket | object | GCS bucket name |
| crdc_series_uuid | object | Alternative series identifier |
| series_size_MB | float64 | Total series size in megabytes |
| series_aws_url | object | S3 URL for series data |
| gcs_bucket_1 | object | Additional GCS bucket field |
| aws_bucket | object | S3 bucket name |
| min_idc_version | Int64 | First IDC version containing this series |
| max_idc_version | Int64 | Last IDC version containing this series |

**Key Differences from `index`:**
- Missing most clinical fields (PatientAge, PatientSex, BodyPartExamined, etc.)
- Has version tracking: min_idc_version, max_idc_version
- Primarily Slide Microscopy (82% of records)

## Modality Codes

### Common Modalities

| Code | Name | Percentage | Description |
|------|------|------------|-------------|
| SR | Structured Report | 27.7% | DICOM structured reports |
| CT | Computed Tomography | 26.0% | X-ray CT scans |
| SEG | Segmentation | 17.2% | Segmentation objects |
| MR | Magnetic Resonance | 12.8% | MRI scans |
| SM | Slide Microscopy | 7.3% | Whole slide imaging |
| MG | Mammography | 5.0% | Mammogram images |
| PT | Positron Emission Tomography | <1% | PET scans |

### Less Common Modalities
- CR: Computed Radiography
- ANN: Annotation
- RTSTRUCT: Radiation Therapy Structure Set
- DX: Digital Radiography
- M3D: Model for 3D Manufacturing
- US: Ultrasound
- PR: Presentation State
- RTDOSE: Radiation Therapy Dose
- NM: Nuclear Medicine
- OT: Other
- RTPLAN: Radiation Therapy Plan

## Body Part Values

### Top Body Parts Examined

| Body Part | Percentage | Series Count |
|-----------|------------|--------------|
| CHEST | 36.8% | ~198,000 |
| BREAST | 11.1% | ~59,000 |
| PROSTATE | 2.4% | ~13,000 |

**Note**: 426,872 series (44.2%) have NULL BodyPartExamined

## Top Collections

| Collection | Series Count | Percentage |
|------------|--------------|------------|
| nlst | 587,799 | 60.9% |
| ispy2 | 32,411 | 3.4% |
| gtex | 25,503 | 2.6% |
| breast_cancer_screening_dbt | 22,032 | 2.3% |
| prostatex | 18,832 | 2.0% |
| acrin_6698 | 18,747 | 1.9% |
| covid_19_ny_sbu | 17,950 | 1.9% |
| lidc_idri | 15,116 | 1.6% |
| ea1141 | 14,340 | 1.5% |
| prostate_mri_us_biopsy | 10,373 | 1.1% |

## License Types

Available licenses (from license_short_name):
- CC BY 3.0
- CC BY 4.0
- CC BY-NC 4.0
- TCIA Restricted
- Custom licenses

## Series Size Statistics

- **Range**: <1 MB to many GB
- **Median**: Varies by modality
- **Recommendation**: 
  - Testing: <100 MB
  - Quick analysis: <30 MB
  - Production: Check series_size_MB before batch downloads

## Null Value Summary

High null counts in clinical fields:
- PatientAge: 773,451 nulls (80%)
- PatientSex: 668,572 nulls (69%)
- BodyPartExamined: 426,872 nulls (44%)
- SeriesDate: 287,330 nulls (30%)
- analysis_result_id: 552,087 nulls (57%)

Columns with no nulls:
- All identifier columns (SeriesInstanceUID, StudyInstanceUID, PatientID, collection_id)
- Modality
- Data access columns (aws_bucket, series_aws_url, series_size_MB, etc.)
