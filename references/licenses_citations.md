# Licenses and Citations Guide

This reference covers checking data licenses and generating proper citations for IDC data.

## License Types in IDC

| License | Commercial Use | Percentage |
|---------|----------------|------------|
| CC BY 4.0 | Yes (with attribution) | ~97% |
| CC BY 3.0 | Yes (with attribution) | Small |
| CC BY-NC 4.0 | No (non-commercial only) | ~3% |
| CC BY-NC 3.0 | No (non-commercial only) | Small |
| Custom | Varies | Rare |

**Important:** Always check the license before using IDC data in publications or commercial applications.

## Querying by License

### Check licenses for all collections

```python
from idc_index import IDCClient

client = IDCClient()

licenses = client.sql_query("""
    SELECT DISTINCT
        collection_id,
        license_short_name,
        COUNT(DISTINCT SeriesInstanceUID) as series_count
    FROM index
    GROUP BY collection_id, license_short_name
    ORDER BY collection_id
""")
print(licenses)
```

### Find only commercially-usable data

```python
# CC BY licenses allow commercial use with attribution
cc_by_data = client.sql_query("""
    SELECT SeriesInstanceUID, collection_id, Modality
    FROM index
    WHERE license_short_name LIKE 'CC BY%'
      AND license_short_name NOT LIKE '%NC%'
      AND Modality = 'CT'
    LIMIT 100
""")
```

### Find non-commercial data

```python
nc_data = client.sql_query("""
    SELECT DISTINCT collection_id, license_short_name
    FROM index
    WHERE license_short_name LIKE '%NC%'
""")
```

## Generating Citations

The `source_DOI` column contains DOIs for data attribution. Use `citations_from_selection()` to generate formatted citations:

### Basic usage

```python
from idc_index import IDCClient

client = IDCClient()

# Citations for a collection (APA format by default)
citations = client.citations_from_selection(collection_id="rider_pilot")
for citation in citations:
    print(citation)
```

### Citations for specific series

```python
results = client.sql_query("""
    SELECT SeriesInstanceUID FROM index
    WHERE collection_id = 'tcga_luad' LIMIT 5
""")

citations = client.citations_from_selection(
    seriesInstanceUID=list(results['SeriesInstanceUID'].values)
)
```

### Citation Formats

```python
# APA format (default)
citations = client.citations_from_selection(
    collection_id="tcga_luad",
    citation_format=IDCClient.CITATION_FORMAT_APA
)

# BibTeX (for LaTeX documents)
bibtex = client.citations_from_selection(
    collection_id="tcga_luad",
    citation_format=IDCClient.CITATION_FORMAT_BIBTEX
)

# JSON (CSL JSON format)
json_citations = client.citations_from_selection(
    collection_id="tcga_luad",
    citation_format=IDCClient.CITATION_FORMAT_JSON
)

# RDF Turtle
turtle = client.citations_from_selection(
    collection_id="tcga_luad",
    citation_format=IDCClient.CITATION_FORMAT_TURTLE
)
```

### Available formats

| Format Constant | Output |
|-----------------|--------|
| `CITATION_FORMAT_APA` | APA style (default) |
| `CITATION_FORMAT_BIBTEX` | BibTeX for LaTeX |
| `CITATION_FORMAT_JSON` | CSL JSON |
| `CITATION_FORMAT_TURTLE` | RDF Turtle |

### Filter parameters

| Parameter | Description |
|-----------|-------------|
| `collection_id` | Filter by collection(s) |
| `patientId` | Filter by patient ID(s) |
| `studyInstanceUID` | Filter by study UID(s) |
| `seriesInstanceUID` | Filter by series UID(s) |

## Best Practices for Attribution

1. **Always cite data sources** - Include citations in publications using IDC data

2. **Save citations with downloads** - Generate and store citations alongside your data:
   ```python
   citations = client.citations_from_selection(collection_id="tcga_luad")
   with open("data/CITATIONS.txt", "w") as f:
       f.write("\n\n".join(citations))
   ```

3. **Check license compatibility** - Ensure your use case is permitted:
   - Academic research: Usually all licenses work
   - Commercial applications: Avoid NC (non-commercial) licenses
   - Redistribution: Check specific license terms

4. **Document license in manifests** - Include license info when sharing data selections:
   ```python
   manifest = client.sql_query("""
       SELECT SeriesInstanceUID, license_short_name, source_DOI
       FROM index
       WHERE collection_id = 'tcga_luad'
   """)
   manifest.to_csv("manifest_with_licenses.csv", index=False)
   ```

## IDC Citation

When using any IDC data, also cite IDC itself:

> Fedorov, A., et al. "National Cancer Institute Imaging Data Commons: Toward Transparency, Reproducibility, and Scalability in Imaging Artificial Intelligence." RadioGraphics 43.12 (2023). https://doi.org/10.1148/rg.230180
