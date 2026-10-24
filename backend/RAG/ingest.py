"""Index curated public agricultural references in a local SQLite FTS5 table.

Expected data/knowledge.json format:
{
  "documents": [
    {
      "title": "A verified public reference title",
      "source_url": "https://example.org/source-page",
      "public": true,
      "passages": ["Short passage copied or paraphrased with permission."]
    }
  ]
}

The `public` flag records YOUR review of the source: this module cannot
establish copyright permissions, source credibility, or provenance itself.
It makes no HTTP requests and must not ingest confidential farm records.

Run from the project root:
    python -m backend.RAG.ingest
Or with an explicit source:
    python -m backend.RAG.ingest --source data/knowledge.json
"""

from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit
from backend import databases

project_root = Path(__file__).resolve().parents[2]
default_knowledge_path = project_root / "data" / "knowledge.json"
max_source_bytes = 5 * 1024 * 1024
max_chunk_characters = 650
max_documents = 200

class RAGIngestionError(ValueError):
    """A reference file cannot be safely indexed"""

def chunk_text(text: str, max_chars: int = max_chunk_characters) -> list[str]:
    """Split text at word boundaries for small, citable FTS5 passages"""
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for word in words:
        if len(word) > max_chars:
            raise RAGIngestionError("A passage contains a word longer than the chunk limit")
        additional = len(word) + (1 if current else 0)
        if current and current_length + additional > max_chars:
            chunks.append(" ".join(current))
            current = [word]
            current_length = len(word)

        else:
            current.append(word)
            current_length += additional
    if current:
        chunks.append(" ".join(current))
    return chunks

def load_documents(path: Path) -> list[dict]:
    try:
        if path.stat().st_size > max_source_bytes:
            raise RAGIngestionError("knowledge.json exceeds the 5 MB limit.")
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RAGIngestionError(f"Knowledge file not found: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RAGIngestionError(f"Cannot read valid UTF-8 JSON from {path}: {exc}") from exc

    if not isinstance(data, dict) or set(data) != {"documents"}:
        raise RAGIngestionError("Top-level JSON must contain only a 'documents' array.")
    documents = data["documents"]
    if not isinstance(documents, list) or not 1 <= len(documents) <= max_documents:
        raise RAGIngestionError(f"'documents' must contain 1-{max_documents} entries.")

    seen_urls: set[str] = set()
    for index, document in enumerate(documents, start=1):
        if not isinstance(document, dict) or set(document) != {
            "title", "source_url", "public", "passages"
        }:
            raise RAGIngestionError(f"Document {index} has missing or unexpected fields.")

        title = document["title"]
        url = document["source_url"]
        passages = document["passages"]
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160:
            raise RAGIngestionError(f"Document {index} needs a title (1-160 characters).")
        if not isinstance(url, str) or not 1 <= len(url) <= 500:
            raise RAGIngestionError(f"Document {index} needs a source URL (1-500 characters).")
        try:
            parsed = urlsplit(url)
            valid_url = (parsed.scheme in {"https", "http"}
                        and bool(parsed.hostname)
                        and not parsed.username and not parsed.password)

        except ValueError:
            valid_url = False

        if not valid_url:
            raise RAGIngestionError(f"Document {index} has an invalid public source URL.")
        if document["public"] is not True:
            raise RAGIngestionError(f"Document {index} is not marked as reviewed public material.")
        if url in seen_urls:
            raise RAGIngestionError(f"Duplicate source URL in document {index}")
        seen_urls.add(url)
        if not isinstance(passages, list) or not passages:
           raise RAGIngestionError(f"Document {index} needs at least one passage")
        for passage in passages:
            if not isinstance(passage, str) or not passage.strip():
                raise RAGIngestionError(f"Document {index} contains an empty or invalid passage.")

    return documents

# ingest the documents 
def ingest_documents(source_path: str | Path | None = None) -> dict[str, int | str]:
    """Replace only the RAG index; retain privacy settings and security events.

    Input: a JSON path (defaults to data/knowledge.json).
    Output: {documents_indexed, passages_indexed, database_path}.
    Raises: RAGIngestionError on invalid input or unsupported SQLite FTS5.
    """
    source = Path(source_path) if source_path is not None else default_knowledge_path
    documents = load_documents(source)
    rows: list[tuple[str, str, str, str, int]] = []
    for document in documents:
        document_id = hashlib.sha256(document["source_url"].encode("utf-8")).hexdigest()[:24]
        chunk_index = 0
        for passage in document["passages"]:
            for chunk in chunk_text(passage):
                rows.append((document_id, document["title"].strip(),
                             document["source_url"], chunk, chunk_index))
                chunk_index += 1

    # Initialize shared tables without wiping other VigiloForge data.
    databases.init_db()
    db_path = databases.database_path()
    connection = sqlite3.connect(str(db_path), timeout=10)
    try:
        with connection:  # Rolls back the index replacement on SQL failure.
            connection.execute(
                """CREATE VIRTUAL TABLE IF NOT EXISTS rag_passages_fts USING fts5(
                    document_id UNINDEXED,
                    title,
                    source_url UNINDEXED,
                    passage,
                    chunk_index UNINDEXED,
                    tokenize='unicode61'
                )"""
            )
            connection.execute("DELETE FROM rag_passages_fts")
            connection.executemany(
                """INSERT INTO rag_passages_fts
                   (document_id, title, source_url, passage, chunk_index)
                   VALUES (?, ?, ?, ?, ?)""",
                rows,
            )
    except sqlite3.OperationalError as exc:
        raise RAGIngestionError(f"SQLite FTS5 indexing failed: {exc}") from exc
    finally:
        connection.close()

    return {
        "documents_indexed": len(documents),
        "passages_indexed": len(rows),
        "database_path": str(db_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Index reviewed public references into SQLite FTS5.")
    parser.add_argument("--source", type=Path, default=None,
                        help="JSON source path (default: data/knowledge.json)")
    args = parser.parse_args()
    try:
        print(json.dumps(ingest_documents(args.source), indent=2))
    except RAGIngestionError as exc:
        parser.exit(1, f"RAG ingestion error: {exc}\n")


if __name__ == "__main__":
    main()
