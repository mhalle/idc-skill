# Segmentations and Annotations Guide

This reference covers finding and working with segmentations, annotations, and other derived objects in IDC.

## Types of Derived Objects

| Modality | Description | Example Content |
|----------|-------------|-----------------|
| SEG | DICOM Segmentation | Organ/tumor masks |
| RTSTRUCT | Radiotherapy Structure Set | Contours for treatment planning |
| SR | Structured Report | Measurements, findings |
| PR | Presentation State | Display annotations |

## Finding Segmentations by Modality

Not all derived objects belong to analysis result collections. Query by DICOM Modality to find all:

```python
from idc_index import IDCClient

client = IDCClient()

# Find all segmentations and structure sets
derived = client.sql_query("""
    SELECT collection_id, Modality, COUNT(*) as series_count
    FROM index
    WHERE Modality IN ('SEG', 'RTSTRUCT')
    GROUP BY collection_id, Modality
    ORDER BY series_count DESC
""")
print(derived)
```

### Find segmentations for a specific collection

```python
segs = client.sql_query("""
    SELECT SeriesInstanceUID, SeriesDescription, analysis_result_id
    FROM index
    WHERE collection_id = 'tcga_luad' AND Modality = 'SEG'
""")
```

## Using seg_index for Detailed Metadata

The `seg_index` table provides detailed segmentation metadata including algorithm info:

```python
client.fetch_index("seg_index")

# Get segmentation statistics by algorithm
algorithms = client.sql_query("""
    SELECT AlgorithmName, AlgorithmType, COUNT(*) as seg_count
    FROM seg_index
    WHERE AlgorithmName IS NOT NULL
    GROUP BY AlgorithmName, AlgorithmType
    ORDER BY seg_count DESC
    LIMIT 10
""")
print(algorithms)
```

### seg_index columns

| Column | Description |
|--------|-------------|
| `SeriesInstanceUID` | Segmentation series UID |
| `segmented_SeriesInstanceUID` | Source image series UID |
| `AlgorithmName` | Name of segmentation algorithm |
| `AlgorithmType` | AUTOMATIC, SEMIAUTOMATIC, MANUAL |
| `total_segments` | Number of segments in the object |

## Joining Segmentations with Source Images

Link segmentations to their source images using `segmented_SeriesInstanceUID`:

```python
client.fetch_index("seg_index")

# Find segmentations for chest CT
result = client.sql_query("""
    SELECT
        s.SeriesInstanceUID as seg_series,
        s.AlgorithmName,
        s.total_segments,
        s.segmented_SeriesInstanceUID as source_series,
        src.collection_id,
        src.BodyPartExamined
    FROM seg_index s
    JOIN index src ON s.segmented_SeriesInstanceUID = src.SeriesInstanceUID
    WHERE src.Modality = 'CT' AND src.BodyPartExamined = 'CHEST'
    LIMIT 10
""")
```

### Find TotalSegmentator results

```python
ts_results = client.sql_query("""
    SELECT
        seg_info.collection_id,
        COUNT(DISTINCT s.SeriesInstanceUID) as seg_count,
        SUM(s.total_segments) as total_segments
    FROM seg_index s
    JOIN index seg_info ON s.SeriesInstanceUID = seg_info.SeriesInstanceUID
    WHERE s.AlgorithmName LIKE '%TotalSegmentator%'
    GROUP BY seg_info.collection_id
    ORDER BY seg_count DESC
""")
```

## Analysis Results Collections

Curated derived datasets are tracked in `analysis_results_index`:

```python
client.fetch_index("analysis_results_index")

# List all analysis result collections
analysis = client.sql_query("""
    SELECT analysis_result_id, analysis_result_title, Collections, Modalities
    FROM analysis_results_index
""")

# Find analysis results for a specific source collection
tcga_analysis = client.sql_query("""
    SELECT analysis_result_id, analysis_result_title
    FROM analysis_results_index
    WHERE Collections LIKE '%tcga_luad%'
""")
```

### Link series to analysis results

```python
# Find series that are part of analysis results
analysis_series = client.sql_query("""
    SELECT i.SeriesInstanceUID, i.Modality, i.analysis_result_id,
           a.analysis_result_title
    FROM index i
    JOIN analysis_results_index a ON i.analysis_result_id = a.analysis_result_id
    WHERE i.collection_id = 'tcga_luad'
    LIMIT 20
""")
```

## Downloading Segmentations with Source Images

```python
# Find a segmentation and its source
client.fetch_index("seg_index")
pair = client.sql_query("""
    SELECT
        s.SeriesInstanceUID as seg_uid,
        s.segmented_SeriesInstanceUID as source_uid
    FROM seg_index s
    JOIN index src ON s.segmented_SeriesInstanceUID = src.SeriesInstanceUID
    WHERE src.collection_id = 'qin_prostate_repeatability'
    LIMIT 1
""")

# Download both
client.download_from_selection(
    seriesInstanceUID=[pair['seg_uid'].iloc[0], pair['source_uid'].iloc[0]],
    downloadDir="./data/seg_pair"
)
```

## Common Patterns

### Find collections with automatic segmentations

```python
client.fetch_index("seg_index")
auto_segs = client.sql_query("""
    SELECT seg_info.collection_id, COUNT(*) as auto_seg_count
    FROM seg_index s
    JOIN index seg_info ON s.SeriesInstanceUID = seg_info.SeriesInstanceUID
    WHERE s.AlgorithmType = 'AUTOMATIC'
    GROUP BY seg_info.collection_id
    ORDER BY auto_seg_count DESC
""")
```

### Find segmentations by anatomical region

```python
brain_segs = client.sql_query("""
    SELECT
        s.SeriesInstanceUID,
        s.AlgorithmName,
        src.collection_id
    FROM seg_index s
    JOIN index src ON s.segmented_SeriesInstanceUID = src.SeriesInstanceUID
    WHERE src.BodyPartExamined LIKE '%BRAIN%'
    LIMIT 20
""")
```
