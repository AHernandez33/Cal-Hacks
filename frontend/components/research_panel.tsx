"use client";
import { useEffect, useState } from "react";
import { requestJSON } from "../lib/api";
type Library = {
  engine: string;
  passages: number;
  indexed: boolean;
  notice: string;
  sources: { title: string; url: string }[];
};
type Passage = {
  document_id: string;
  title: string;
  source_url: string;
  passage: string;
  chunk_index: number;
};
export default function ResearchPanel() {
  const [library, setLibrary] = useState<Library | null>(null);
  const [query, setQuery] = useState("leaf yellowing irrigation");
  const [results, setResults] = useState<Passage[]>([]);
  const [searched, setSearched] = useState(false);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    requestJSON<Library>("/knowledge/status")
      .then((value) => {
        if (active) setLibrary(value);
      })
      .catch((e) => {
        if (active) setMessage(String(e));
      });
    return () => {
      active = false;
    };
  }, []);
  async function search(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    setSearched(false);
    try {
      const [value, status] = await Promise.all([
        requestJSON<{ results: Passage[] }>(
          `/knowledge/search?query=${encodeURIComponent(query)}&limit=5`,
        ),
        requestJSON<Library>("/knowledge/status"),
      ]);
      setResults(value.results);
      setLibrary(status);
      setSearched(true);
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel">
      <h2>Scientific reference retrieval</h2>
      <p>
        Search public passages stored in the local SQLite FTS5 index. This is
        keyword retrieval, not an LLM answer or a disease diagnosis.
      </p>
      {library && (
        <div className="research-status">
          <strong>{library.passages} searchable passages</strong>
          <p className="muted">{library.notice}</p>
        </div>
      )}
      <form onSubmit={(e) => void search(e)}>
        <label className="field">
          Research question or keywords
          <input
            required
            maxLength={500}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <button disabled={busy || !query.trim()}>
          {busy ? "Searching…" : "Search local scientific library"}
        </button>
      </form>
      {message && (
        <p role="alert" className="error">
          {message}
        </p>
      )}
      {searched && <p role="status">{results.length} matching passages.</p>}
      {results.map((item, i) => (
        <article
          className="research-result"
          key={`${item.document_id}-${item.chunk_index}-${i}`}
        >
          <h3>
            <a href={item.source_url} target="_blank" rel="noreferrer">
              {item.title}
            </a>
          </h3>
          <blockquote>{item.passage}</blockquote>
          <p className="muted">
            Retrieved passage · verify context at the original source.
          </p>
        </article>
      ))}
      {library && library.passages === 0 && (
        <p className="muted">
          No scientific evidence is available yet. The placeholder reference is
          excluded. The project owner must add reviewed public passages and
          rebuild the index.
        </p>
      )}
    </section>
  );
}
