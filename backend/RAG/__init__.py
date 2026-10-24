"""Local public reference RAG (Retrieval augmented generation) package for VigiloForge SCD.

Modules:
- ingest.py - validate and index approved public reference passages
- retrieve.py - search the local SQLite FTS5 index
- pipeline.py - assemble evidence for authorized AI requests

Importing this package NEVER initializes the database or contacts an AI provider
"""

__all__: list[str] = []
