# IDC Collections Database

The skill includes a pre-built SQLite database of IDC collection metadata at `assets/idc_collections.db`. This database provides fast local access to collection information without requiring API calls.

## Database Location

```
assets/idc_collections.db
```

## Schema

### `collections` Table

| Column | Type | Description |
|--------|------|-------------|
| collection_id | TEXT | Primary key, unique collection identifier |
| cancer_type | TEXT | Type of cancer (e.g., "Lung Cancer", "Breast Cancer") |
| location | TEXT | Anatomical location (e.g., "Lung", "Breast", "Brain") |
| species | TEXT | Species (Human, Mouse, Canine, Phantom) |
| subject_count | INTEGER | Number of subjects in the collection |
| date_updated | TEXT | Last update date (YYYY-MM-DD) |
| doi | TEXT | Digital Object Identifier(s) |
| image_types | TEXT | Comma-separated modalities (CT, MR, PT, SM, SEG, etc.) |
| supporting_data | TEXT | Additional data types (Clinical, Genomics, etc.) |
| description | TEXT | Markdown description of the collection |

### `collections_fts` Table

Full-text search virtual table indexing: collection_id, cancer_type, location, species, image_types, supporting_data, description.

### `metadata` Table

| Key | Description |
|-----|-------------|
| schema_version | Database schema version |
| built_at | ISO timestamp when database was built |
| source_url | API URL used to fetch data |

## Query Examples

### Basic Queries

```sql
-- List all collections
SELECT collection_id, cancer_type, subject_count
FROM collections
ORDER BY subject_count DESC;

-- Find collections by cancer type
SELECT collection_id, cancer_type, location, subject_count
FROM collections
WHERE cancer_type LIKE '%Lung%';

-- Find collections by species
SELECT collection_id, cancer_type, species
FROM collections
WHERE species = 'Mouse';

-- Find collections with specific modality
SELECT collection_id, cancer_type, image_types
FROM collections
WHERE image_types LIKE '%MR%';
```

### Full-Text Search

```sql
-- Search across all indexed fields
SELECT collection_id, cancer_type, location
FROM collections_fts
WHERE collections_fts MATCH 'breast';

-- Search with ranking (lower bm25 score = better match)
SELECT collection_id, cancer_type, bm25(collections_fts) as score
FROM collections_fts
WHERE collections_fts MATCH 'lung cancer'
ORDER BY score
LIMIT 10;

-- Search specific column
SELECT collection_id, description
FROM collections_fts
WHERE collections_fts MATCH 'description:MRI';

-- Boolean search
SELECT collection_id, cancer_type
FROM collections_fts
WHERE collections_fts MATCH 'breast AND screening';
```

### Aggregations

```sql
-- Count collections by cancer type
SELECT cancer_type, COUNT(*) as count
FROM collections
GROUP BY cancer_type
ORDER BY count DESC;

-- Count collections by species
SELECT species, COUNT(*) as count, SUM(subject_count) as total_subjects
FROM collections
GROUP BY species;

-- Collections with most subjects
SELECT collection_id, cancer_type, subject_count
FROM collections
ORDER BY subject_count DESC
LIMIT 10;
```

### Get Collection Details

```sql
-- Full details for a specific collection
SELECT * FROM collections
WHERE collection_id = 'tcga_luad';

-- Get description for a collection
SELECT collection_id, description
FROM collections
WHERE collection_id = 'lidc_idri';
```

## Usage in Python

```python
import sqlite3

# Connect to database
conn = sqlite3.connect('assets/idc_collections.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Search for collections
cur.execute("""
    SELECT collection_id, cancer_type, subject_count
    FROM collections_fts
    WHERE collections_fts MATCH ?
    ORDER BY subject_count DESC
""", ('lung',))

for row in cur.fetchall():
    print(f"{row['collection_id']}: {row['cancer_type']} ({row['subject_count']} subjects)")

conn.close()
```

## Notes

- The database is built from the IDC API at build time
- Use this database for quick lookups instead of calling the slow IDC API
- For detailed series-level data, use the `idc-index` Python package
- The description field contains markdown converted from HTML
