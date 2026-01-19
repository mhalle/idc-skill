# IDC Query Patterns

This reference provides comprehensive SQL query examples for common IDC data exploration tasks.

## Query Writing Guidelines

- **Table name**: Always use `index` or `prior_versions_index` (lowercase)
- **SQL dialect**: DuckDB SQL syntax
- **LIMIT clause**: Use LIMIT for initial exploration
- **Null handling**: Check for nulls in clinical fields (see schema_reference.md)
- **Case sensitivity**: Column names are case-sensitive

## Basic Filtering

### Find Series by Modality

```sql
-- Find all CT scans
SELECT * FROM index 
WHERE Modality = 'CT' 
LIMIT 10;

-- Find MR or CT scans
SELECT * FROM index 
WHERE Modality IN ('MR', 'CT') 
LIMIT 10;
```

### Find Series by Body Part

```sql
-- Find chest imaging (handle nulls)
SELECT * FROM index 
WHERE BodyPartExamined LIKE '%CHEST%'
LIMIT 10;

-- Find brain MR scans
SELECT * FROM index 
WHERE Modality = 'MR' 
AND BodyPartExamined = 'BRAIN'
LIMIT 10;
```

### Find Small Series for Quick Analysis

```sql
-- Find series under 50MB
SELECT SeriesInstanceUID, series_size_MB, 
       collection_id, Modality
FROM index 
WHERE series_size_MB < 50
ORDER BY series_size_MB ASC
LIMIT 20;

-- Find MR series under 30MB
SELECT SeriesInstanceUID, series_size_MB, 
       collection_id, BodyPartExamined
FROM index 
WHERE Modality = 'MR' 
AND series_size_MB < 30
ORDER BY series_size_MB ASC
LIMIT 10;
```

## Collection Queries

### Explore a Specific Collection

```sql
-- Get all series in a collection
SELECT * FROM index 
WHERE collection_id = 'tcga_luad'
LIMIT 10;

-- Count series by modality in a collection
SELECT Modality, COUNT(*) as series_count
FROM index
WHERE collection_id = 'tcga_luad'
GROUP BY Modality
ORDER BY series_count DESC;

-- Get collection statistics
SELECT collection_id,
       COUNT(*) as series_count,
       SUM(series_size_MB) as total_mb,
       AVG(series_size_MB) as avg_mb,
       MIN(series_size_MB) as min_mb,
       MAX(series_size_MB) as max_mb
FROM index
WHERE collection_id = 'tcga_luad'
GROUP BY collection_id;
```

### List All Collections

```sql
-- Get all collections with series counts
SELECT collection_id, 
       COUNT(*) as series_count,
       SUM(series_size_MB) as total_size_mb
FROM index
GROUP BY collection_id
ORDER BY series_count DESC;
```

## Patient and Study Queries

### Find Studies for a Patient

```sql
-- Get all studies for a patient
SELECT DISTINCT StudyInstanceUID, StudyDate, StudyDescription
FROM index 
WHERE PatientID = 'PATIENT-001'
ORDER BY StudyDate;

-- Get series grouped by study for a patient
SELECT StudyInstanceUID, StudyDate,
       COUNT(*) as series_count,
       SUM(series_size_MB) as total_mb
FROM index
WHERE PatientID = 'PATIENT-001'
GROUP BY StudyInstanceUID, StudyDate
ORDER BY StudyDate;
```

### Find Series for a Study

```sql
-- Get all series in a study
SELECT SeriesInstanceUID, SeriesNumber, 
       Modality, SeriesDescription,
       series_size_MB
FROM index
WHERE StudyInstanceUID = '1.2.3.4.5.6.7.8.9'
ORDER BY SeriesNumber;
```

## Date Range Filtering

### Find Series by Date

```sql
-- Find series from specific year
SELECT * FROM index 
WHERE StudyDate >= '2020-01-01' 
AND StudyDate <= '2020-12-31'
AND Modality = 'CT'
LIMIT 10;

-- Find recent series (handle nulls in SeriesDate)
SELECT * FROM index 
WHERE SeriesDate >= '2023-01-01'
AND SeriesDate IS NOT NULL
LIMIT 10;

-- Find series from last 5 years of study dates
SELECT * FROM index
WHERE StudyDate >= '2020-01-01'
ORDER BY StudyDate DESC
LIMIT 10;
```

## Aggregation Queries

### Count by Modality and Body Part

```sql
-- Series count by modality
SELECT Modality, 
       COUNT(*) as series_count,
       AVG(series_size_MB) as avg_size_mb
FROM index
GROUP BY Modality
ORDER BY series_count DESC;

-- Cross-tabulation of modality and body part
SELECT Modality, BodyPartExamined, 
       COUNT(*) as count
FROM index
WHERE BodyPartExamined IS NOT NULL
GROUP BY Modality, BodyPartExamined
ORDER BY count DESC
LIMIT 20;
```

### Manufacturer Statistics

```sql
-- Count by manufacturer
SELECT Manufacturer, 
       COUNT(*) as series_count,
       COUNT(DISTINCT ManufacturerModelName) as model_count
FROM index
WHERE Manufacturer IS NOT NULL
GROUP BY Manufacturer
ORDER BY series_count DESC
LIMIT 10;

-- Specific manufacturer models
SELECT Manufacturer, ManufacturerModelName, 
       COUNT(*) as series_count
FROM index
WHERE Manufacturer = 'SIEMENS'
GROUP BY Manufacturer, ManufacturerModelName
ORDER BY series_count DESC;
```

### Patient Demographics

```sql
-- Count by patient sex (handle nulls)
SELECT PatientSex, COUNT(*) as series_count
FROM index
WHERE PatientSex IS NOT NULL
GROUP BY PatientSex;

-- Age distribution (handle nulls and format)
SELECT PatientAge, COUNT(*) as series_count
FROM index
WHERE PatientAge IS NOT NULL
GROUP BY PatientAge
ORDER BY PatientAge
LIMIT 20;
```

## Instance Count Queries

### Find Series by Instance Count

```sql
-- Find series with specific number of images
SELECT SeriesInstanceUID, instanceCount, 
       Modality, series_size_MB
FROM index
WHERE instanceCount >= 50 
AND instanceCount <= 200
ORDER BY instanceCount DESC
LIMIT 10;

-- Average instances per series by modality
SELECT Modality, 
       AVG(instanceCount) as avg_instances,
       MIN(instanceCount) as min_instances,
       MAX(instanceCount) as max_instances
FROM index
GROUP BY Modality
ORDER BY avg_instances DESC;
```

## Historical Data Queries (prior_versions_index)

### Find Removed Series

```sql
-- Find series removed in recent versions
SELECT collection_id, Modality, 
       min_idc_version, max_idc_version,
       COUNT(*) as series_count
FROM prior_versions_index
WHERE max_idc_version >= 20
GROUP BY collection_id, Modality, min_idc_version, max_idc_version
ORDER BY series_count DESC;

-- Find collections with removed series
SELECT collection_id, 
       COUNT(*) as removed_series,
       SUM(series_size_MB) as removed_size_mb
FROM prior_versions_index
GROUP BY collection_id
ORDER BY removed_series DESC
LIMIT 10;
```

### Join Current and Historical Data

```sql
-- Compare current vs historical series counts
SELECT 
    COALESCE(i.collection_id, p.collection_id) as collection,
    COUNT(DISTINCT i.SeriesInstanceUID) as current_series,
    COUNT(DISTINCT p.SeriesInstanceUID) as historical_series
FROM index i
FULL OUTER JOIN prior_versions_index p 
    ON i.collection_id = p.collection_id
GROUP BY collection
ORDER BY current_series DESC NULLS LAST
LIMIT 10;

-- Find collections that had data removed
SELECT 
    p.collection_id,
    COUNT(DISTINCT p.SeriesInstanceUID) as removed_series,
    COUNT(DISTINCT i.SeriesInstanceUID) as current_series
FROM prior_versions_index p
LEFT JOIN index i ON i.collection_id = p.collection_id
GROUP BY p.collection_id
HAVING COUNT(DISTINCT p.SeriesInstanceUID) > 0
ORDER BY removed_series DESC
LIMIT 10;
```

## Complex Multi-Criteria Queries

### Find Ideal Series for Analysis

```sql
-- Find small, complete brain MR series with clinical data
SELECT SeriesInstanceUID, series_size_MB,
       collection_id, PatientAge, PatientSex,
       StudyDate, SeriesDescription
FROM index
WHERE Modality = 'MR'
AND BodyPartExamined = 'BRAIN'
AND series_size_MB < 50
AND PatientAge IS NOT NULL
AND PatientSex IS NOT NULL
AND instanceCount >= 20
ORDER BY series_size_MB ASC
LIMIT 10;

-- Find diverse training dataset samples
SELECT collection_id, Modality, BodyPartExamined,
       COUNT(*) as series_count,
       AVG(series_size_MB) as avg_size_mb
FROM index
WHERE series_size_MB < 100
AND BodyPartExamined IS NOT NULL
GROUP BY collection_id, Modality, BodyPartExamined
HAVING COUNT(*) >= 5
ORDER BY series_count DESC
LIMIT 20;
```

### License-Aware Queries

```sql
-- Find openly licensed data
SELECT license_short_name, 
       COUNT(*) as series_count,
       SUM(series_size_MB) as total_mb
FROM index
WHERE license_short_name LIKE 'CC BY%'
GROUP BY license_short_name;

-- Find series with specific license
SELECT * FROM index
WHERE license_short_name = 'CC BY 4.0'
AND Modality = 'CT'
LIMIT 10;
```

## Data Quality Queries

### Check Null Patterns

```sql
-- Count nulls by column
SELECT 
    COUNT(*) as total_series,
    COUNT(PatientAge) as has_age,
    COUNT(PatientSex) as has_sex,
    COUNT(BodyPartExamined) as has_body_part,
    COUNT(SeriesDescription) as has_series_desc
FROM index;

-- Find series with complete clinical data
SELECT * FROM index
WHERE PatientAge IS NOT NULL
AND PatientSex IS NOT NULL
AND BodyPartExamined IS NOT NULL
AND StudyDescription IS NOT NULL
LIMIT 10;
```

### Find Duplicate or Similar Series

```sql
-- Find patients with multiple studies
SELECT PatientID, 
       COUNT(DISTINCT StudyInstanceUID) as study_count,
       COUNT(*) as total_series
FROM index
GROUP BY PatientID
HAVING COUNT(DISTINCT StudyInstanceUID) > 1
ORDER BY study_count DESC
LIMIT 10;

-- Find series with same description
SELECT SeriesDescription, 
       COUNT(*) as count
FROM index
WHERE SeriesDescription IS NOT NULL
GROUP BY SeriesDescription
ORDER BY count DESC
LIMIT 20;
```

## Performance Tips

1. **Use LIMIT** for initial exploration to avoid large result sets
2. **Filter early** - Apply WHERE clauses before joins and aggregations
3. **Check for nulls** - Many clinical fields have high null counts
4. **Index columns** - SeriesInstanceUID, collection_id are most selective
5. **Size filtering** - Always consider series_size_MB for download planning
