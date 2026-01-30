# /// script
# dependencies = [
#   "httpx",
#   "markdownify",
# ]
# ///
"""
Build SQLite database with FTS from IDC collections API.

Usage:
    uv run build_collections_db.py [output.db]
"""

import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import markdownify

API_URL = "https://api.imaging.datacommons.cancer.gov/v2/collections"
DEFAULT_OUTPUT = "idc_collections.db"
SCHEMA_VERSION = 1


def fetch_collections() -> list[dict]:
    """Fetch collections from IDC API."""
    print(f"Fetching from {API_URL}...")
    print("(This endpoint is slow, please wait)")

    with httpx.Client(timeout=120.0) as client:
        response = client.get(API_URL)
        response.raise_for_status()
        data = response.json()

    print(f"Fetched {len(data['collections'])} collections")
    return data["collections"]


def html_to_markdown(html: str) -> str:
    """Convert HTML description to markdown."""
    if not html:
        return ""
    # Fix: convert url= to href= for links with empty href
    html = re.sub(r'href="" url="([^"]+)"', r'href="\1"', html)
    return markdownify.markdownify(html, strip=["i"]).strip()


def create_database(db_path: Path, collections: list[dict]):
    """Create SQLite database with FTS."""
    print(f"Creating database: {db_path}")

    # Remove existing database for clean rebuild
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create metadata table
    cur.execute("""
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cur.execute("INSERT INTO metadata (key, value) VALUES (?, ?)",
                ("schema_version", str(SCHEMA_VERSION)))
    cur.execute("INSERT INTO metadata (key, value) VALUES (?, ?)",
                ("built_at", datetime.now(timezone.utc).isoformat()))
    cur.execute("INSERT INTO metadata (key, value) VALUES (?, ?)",
                ("source_url", API_URL))

    # Create main collections table
    cur.execute("""
        CREATE TABLE collections (
            collection_id TEXT PRIMARY KEY,
            cancer_type TEXT,
            location TEXT,
            species TEXT,
            subject_count INTEGER,
            date_updated TEXT,
            doi TEXT,
            image_types TEXT,
            supporting_data TEXT,
            description TEXT
        )
    """)

    # Create FTS virtual table
    cur.execute("""
        CREATE VIRTUAL TABLE collections_fts USING fts5(
            collection_id,
            cancer_type,
            location,
            species,
            image_types,
            supporting_data,
            description,
            content='collections',
            content_rowid='rowid'
        )
    """)

    # Insert data
    for coll in collections:
        description = html_to_markdown(coll.get("description", ""))

        cur.execute("""
            INSERT INTO collections (
                collection_id, cancer_type, location, species, subject_count,
                date_updated, doi, image_types, supporting_data, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            coll.get("collection_id"),
            coll.get("cancer_type"),
            coll.get("location"),
            coll.get("species"),
            coll.get("subject_count"),
            coll.get("date_updated"),
            coll.get("doi"),
            coll.get("image_types"),
            coll.get("supporting_data"),
            description,
        ))

    # Populate FTS index
    cur.execute("""
        INSERT INTO collections_fts (
            rowid, collection_id, cancer_type, location, species,
            image_types, supporting_data, description
        )
        SELECT rowid, collection_id, cancer_type, location, species,
               image_types, supporting_data, description
        FROM collections
    """)

    # Create triggers to keep FTS in sync
    cur.execute("""
        CREATE TRIGGER collections_ai AFTER INSERT ON collections BEGIN
            INSERT INTO collections_fts (
                rowid, collection_id, cancer_type, location, species,
                image_types, supporting_data, description
            ) VALUES (
                new.rowid, new.collection_id, new.cancer_type, new.location,
                new.species, new.image_types, new.supporting_data, new.description
            );
        END
    """)

    cur.execute("""
        CREATE TRIGGER collections_ad AFTER DELETE ON collections BEGIN
            INSERT INTO collections_fts (
                collections_fts, rowid, collection_id, cancer_type, location,
                species, image_types, supporting_data, description
            ) VALUES (
                'delete', old.rowid, old.collection_id, old.cancer_type,
                old.location, old.species, old.image_types, old.supporting_data,
                old.description
            );
        END
    """)

    cur.execute("""
        CREATE TRIGGER collections_au AFTER UPDATE ON collections BEGIN
            INSERT INTO collections_fts (
                collections_fts, rowid, collection_id, cancer_type, location,
                species, image_types, supporting_data, description
            ) VALUES (
                'delete', old.rowid, old.collection_id, old.cancer_type,
                old.location, old.species, old.image_types, old.supporting_data,
                old.description
            );
            INSERT INTO collections_fts (
                rowid, collection_id, cancer_type, location, species,
                image_types, supporting_data, description
            ) VALUES (
                new.rowid, new.collection_id, new.cancer_type, new.location,
                new.species, new.image_types, new.supporting_data, new.description
            );
        END
    """)

    conn.commit()

    # Summary
    cur.execute("SELECT COUNT(*) FROM collections")
    count = cur.fetchone()[0]
    print(f"Inserted {count} collections")

    conn.close()
    print(f"Database created: {db_path} ({db_path.stat().st_size / 1024:.1f} KB)")


def main():
    output = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT)
    collections = fetch_collections()
    create_database(output, collections)


if __name__ == "__main__":
    main()
