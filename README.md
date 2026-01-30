# idc-skill

A skill for exploring cancer imaging data from the [Imaging Data Commons (IDC)](https://portal.imaging.datacommons.cancer.gov/), a cloud-based repository of publicly available cancer imaging data.

## About IDC

The Imaging Data Commons is an NCI Cancer Research Data Commons resource providing access to:
- **Hundreds of thousands of DICOM series** across **160+ collections**
- Cancer imaging from major research initiatives (TCGA, NLST, LIDC-IDRI, and more)
- Multiple modalities: CT, MRI, PET, pathology slides, and derived analysis results
- Clinical, genomic, and histopathology supporting data

### IDC Resources

- [IDC Portal](https://portal.imaging.datacommons.cancer.gov/) - Browse and explore collections
- [IDC Documentation](https://learn.canceridc.dev/) - Tutorials and guides
- [IDC GitHub](https://github.com/ImagingDataCommons) - Tools and code
- [idc-index Python Package](https://pypi.org/project/idc-index/) - Programmatic access to IDC data

## Features

This skill enables Claude to:

- **Browse collections** - Search and filter imaging collections by cancer type, body location, species, or keywords
- **Query imaging metadata** - Find specific DICOM series by modality, body part, size, or clinical criteria
- **Generate download scripts** - Create ready-to-run Python scripts for downloading DICOM data
- **Analyze DICOM files** - Read and interpret DICOM metadata and pixel data
- **Visualize data** - Preview imaging in OHIF/SLIM viewers without downloads
- **Work in restricted environments** - Adapts workflows for environments with limited network access

## Example Queries

Once installed, you can ask questions like:

- "What lung cancer imaging collections are available in IDC?"
- "Find brain MRI datasets with fewer than 50 subjects"
- "Show me collections that include both CT scans and genomic data"
- "Help me download chest CT scans under 100MB for analysis"
- "What modalities are available in the TCGA-LUAD collection?"
- "Find collections with mouse imaging data"
- "Search IDC for breast cancer screening studies"

## Installation

### Download from GitHub Releases

The latest release is always available at:
[https://github.com/mhalle/idc-skill/releases/latest/download/idc-skill.skill](https://github.com/mhalle/idc-skill/releases/latest/download/idc-skill.skill)

All versioned releases can be found at:
[https://github.com/mhalle/idc-skill/releases](https://github.com/mhalle/idc-skill/releases)

### Claude Code

Download and extract to your `.claude/skills/` directory:

**Project-level** (applies to a specific project):
```bash
curl -LO https://github.com/mhalle/idc-skill/releases/latest/download/idc-skill.skill
unzip idc-skill.skill -d /path/to/your/project/.claude/skills/
```

**User-level** (applies globally):
```bash
curl -LO https://github.com/mhalle/idc-skill/releases/latest/download/idc-skill.skill
unzip idc-skill.skill -d ~/.claude/skills/
```

Or clone the repository directly:
```bash
git clone https://github.com/mhalle/idc-skill.git ~/.claude/skills/idc-skill
```

### Claude Platform

1. Download the latest `.skill` file from [GitHub Releases](https://github.com/mhalle/idc-skill/releases/latest)

2. Upload `idc-skill.skill` through the Claude platform skill installation interface.

## Checking for Updates

The installed skill version is stored in the `metadata.version` field of `SKILL.md`.

To check for updates, compare your installed version against the latest release:

```bash
# Get latest release version from GitHub
curl -s https://api.github.com/repos/mhalle/idc-skill/releases/latest | grep '"tag_name"'
```

**Note:** Automatic version checking requires platform support. The skill includes its version in the frontmatter metadata, but discovering the installed version programmatically depends on the host environment's capabilities.

See [references/updating.md](references/updating.md) for detailed update procedures.

## Usage

Once installed, the skill is triggered automatically when you mention:
- IDC
- Imaging Data Commons
- IDC collections

You can also invoke it directly with `/idc-skill`.

## Contents

- [SKILL.md](SKILL.md) - Main skill instructions and workflows
- [references/schema_reference.md](references/schema_reference.md) - Database schema documentation
- [references/query_patterns.md](references/query_patterns.md) - SQL query examples
- [references/collections_database.md](references/collections_database.md) - Local collections database schema and queries
- [references/updating.md](references/updating.md) - Detailed update procedures for different platforms
- [references/index_tables.md](references/index_tables.md) - All 8 index tables, joins, and schema discovery
- [references/downloads.md](references/downloads.md) - Download API, CLI, templates, and manifests
- [references/licenses_citations.md](references/licenses_citations.md) - License checking and citation generation
- [references/segmentations.md](references/segmentations.md) - Finding segmentations and annotations
- [references/analysis_pipelines.md](references/analysis_pipelines.md) - Integration with pydicom, SimpleITK, and analysis workflows
- [references/bigquery_guide.md](references/bigquery_guide.md) - Advanced BigQuery access for full DICOM metadata
- [references/dicomweb_guide.md](references/dicomweb_guide.md) - DICOMweb API access for PACS integration
- [references/viewers_guide.md](references/viewers_guide.md) - Browser-based OHIF/SLIM viewer usage
- [assets/idc_collections.db](assets/idc_collections.db) - Pre-built SQLite database of IDC collection metadata

## Developer

### Releasing a New Version

The version number in `SKILL.md` (under `metadata.version`) must be kept in sync with the git tag.

When releasing:

1. Update `metadata.version` in `SKILL.md` to match the new version
2. Commit the change
3. Create a matching git tag (with `v` prefix):
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

The GitHub Actions workflow will automatically package and publish the `.skill` files when a tag is pushed.

### Rebuilding the Collections Database

The `assets/idc_collections.db` database is built from the IDC API. Rebuild it periodically to pick up new collections:

```bash
uv run scripts/utils/build_collections_db.py assets/idc_collections.db
```

The API endpoint is slow (30-60 seconds). The script is idempotent and will replace any existing database. Commit the updated database after rebuilding.

See [scripts/utils/README.md](scripts/utils/README.md) for more details.
