
"""Search the local SQLite FTS5 index built by backend.RAG.ingest.

Run from the project root:
    python -m backend.RAG.retrieve "leaf discoloration"

Only text already indexed from curated public-reference JSON is retrieved.
This module does not access external services or private farm records.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3

from backend import databases

MAX_QUERY_LENGTH = 500
MAX_QUERY_TERMS = 12
MAX_RESULTS = 10


class RAGRetrievalError(RuntimeError):
    """Raised when the local RAG index is missing or a query cannot be run."""


def _fts_query(text: str) -> str:
    """Turn ordinary search text into a safe FTS5 OR expression.

    Quoting each token prevents user-supplied FTS5 operators from being
    interpreted as syntax. The query is also passed as a SQL parameter.
    """
    if not isinstance(text, str) or not text.strip():
        raise RAGRetrievalError("Provide a nonempty search query.")
    if len(text) > MAX_QUERY_LENGTH:
        raise RAGRetrievalError("Search query is too long (500-character maximum).")

    words = re.findall(r"[A-Za-z0-9]{2,}", text.lower())
    unique_words = list(dict.fromkeys(words))[:MAX_QUERY_TERMS]
    if not unique_words:
        raise RAGRetrievalError("Search query contains no searchable words.")

    return " OR ".join(f'"{word}"' for word in unique_words)


def search_documents(query: str, limit: int = 5) -> list[dict]:
    """Return ranked matching passages with their citation metadata.

    Inputs:
        query: plain-English public-reference search query.
        limit: 1 to 10 passages, default 5.

    Outputs: list of dicts, each with document_id, title, source_url,
        passage, chunk_index, and bm25_score. A *lower* BM25 score ranks
        earlier; the number is not a probability or scientific confidence.

    If the index is missing, run `python -m backend.RAG.ingest` first.
    """
    if type(limit) is not int or not 1 <= limit <= MAX_RESULTS:
        raise RAGRetrievalError("limit must be an integer from 1 to 10.")

    expression = _fts_query(query)
    databases.init_db()  # Initializes shared SQLite settings safely, if needed.

    connection = sqlite3.connect(str(databases.database_path()), timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'rag_passages_fts'"
        ).fetchone()
        if not exists:
            raise RAGRetrievalError(
                "RAG index not found. Run: python -m backend.RAG.ingest"
            )

        rows = connection.execute(
            """
            SELECT document_id, title, source_url, passage, chunk_index,
                   bm25(rag_passages_fts) AS bm25_score
            FROM rag_passages_fts
            WHERE rag_passages_fts MATCH ?
            ORDER BY bm25_score ASC
            LIMIT ?
            """,
            (expression, limit),
        ).fetchall()
    except sqlite3.Error as exc:
        raise RAGRetrievalError(f"SQLite RAG search failed: {exc}") from exc
    finally:
        connection.close()

    return [
        {
            "document_id": row["document_id"],
            "title": row["title"],
            "source_url": row["source_url"],
            "passage": row["passage"],
            "chunk_index": int(row["chunk_index"]),
            "bm25_score": float(row["bm25_score"]),
        }
        for row in rows
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search local agricultural references.")
    parser.add_argument("query", help="Search terms, e.g. 'leaf yellowing'")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    try:
        results = search_documents(args.query, args.limit)
    except RAGRetrievalError as exc:
        parser.exit(1, f"RAG retrieval error: {exc}\n")

    print(json.dumps({"count": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    main()
