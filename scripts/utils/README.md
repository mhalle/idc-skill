# Utility Scripts

These scripts are used for building and maintaining skill assets. They are intended to be run at build time by developers, not by the LLM during skill execution.

## build_collections_db.py

Fetches IDC collection metadata from the API and builds a SQLite database with full-text search support.

### Usage

```bash
cd scripts/utils
uv run build_collections_db.py ../../assets/idc_collections.db
```

Or from the repository root:

```bash
uv run scripts/utils/build_collections_db.py assets/idc_collections.db
```

### Output

The script creates a SQLite database at `assets/idc_collections.db` containing:

- **`collections`** table - All IDC collection metadata with markdown descriptions
- **`collections_fts`** table - Full-text search index
- **`metadata`** table - Build timestamp, schema version, and source URL

### Notes

- The IDC API endpoint is slow; expect the fetch to take 30-60 seconds
- The script is idempotent and will replace any existing database
- The database should be committed to the repository after rebuilding
- **This script should not be invoked by the LLM** - the pre-built database in `assets/` should be used instead
