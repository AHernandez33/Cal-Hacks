import { Fragment, type ReactNode } from "react";

/** Hosted outputs may contain JSON encoded again inside a text/result field. */
export function decodeReport(value: unknown): unknown {
  let decoded = value;
  for (let attempt = 0; attempt < 8 && typeof decoded === "string"; attempt++) {
    const text = decoded.trim();
    const fenced = text.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?```$/i);
    const candidate = fenced ? fenced[1].trim() : text;
    if (!/^[{[\"]/.test(candidate)) break;
    try {
      const next: unknown = JSON.parse(candidate);
      if (next === decoded) break;
      decoded = next;
    } catch { break; }
  }
  return decoded;
}

function label(key: string) {
  const words = key.replace(/([a-z0-9])([A-Z])/g, "$1 $2").replace(/[_-]+/g, " ").trim();
  return words ? words[0].toUpperCase() + words.slice(1) : "Details";
}

// Render only safe text/React elements; agent output never becomes raw HTML.
function inline(text: string): ReactNode {
  return text.split(/(\*\*[^*\n]+\*\*|\[[^\]\n]+\]\(https?:\/\/[^\s)]+\))/g).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
    const link = part.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
    if (link) return <a key={index} href={link[2]} target="_blank" rel="noreferrer">{link[1]}</a>;
    return <Fragment key={index}>{part}</Fragment>;
  });
}

function prose(text: string): ReactNode[] | ReactNode {
  const fences = [...text.matchAll(/```(?:json)?[ \t]*\r?\n([\s\S]*?)```/gi)];
  if (fences.length) {
    const parts: ReactNode[] = [];
    let cursor = 0;
    for (const [index, fence] of fences.entries()) {
      const start = fence.index ?? cursor;
      if (start > cursor) parts.push(<Fragment key={`before-${index}`}>{prose(text.slice(cursor, start))}</Fragment>);
      const decoded = decodeReport(fence[0]);
      parts.push(decoded === fence[0]
        ? <p key={`block-${index}`}>{fence[1]}</p>
        : <ReportValue key={`block-${index}`} value={decoded} />);
      cursor = start + fence[0].length;
    }
    if (cursor < text.length) parts.push(<Fragment key="after">{prose(text.slice(cursor))}</Fragment>);
    return parts;
  }
  if (/^[a-z]+(?:_[a-z0-9]+)+$/.test(text)) text = label(text);
  if (/^https?:\/\/\S+$/.test(text.trim()))
    return <p><a href={text.trim()} target="_blank" rel="noreferrer">{text.trim()}</a></p>;
  const lines = text.replace(/\r\n?/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  for (let index = 0; index < lines.length;) {
    const line = lines[index].trim();
    if (!line) { index++; continue; }
    const heading = line.match(/^#{1,6}\s+(.+)$/);
    if (heading) { blocks.push(<h5 key={index}>{inline(heading[1])}</h5>); index++; continue; }
    const list = line.match(/^(?:[-*+]\s+|\d+[.)]\s+)(.+)$/);
    if (list) {
      const start = index;
      const numbered = /^\d/.test(line);
      const items: ReactNode[] = [];
      while (index < lines.length) {
        const entry = lines[index].trim().match(numbered ? /^\d+[.)]\s+(.+)$/ : /^[-*+]\s+(.+)$/);
        if (!entry) break;
        items.push(<li key={index}>{inline(entry[1])}</li>);
        index++;
      }
      blocks.push(numbered ? <ol key={start}>{items}</ol> : <ul key={start}>{items}</ul>);
      continue;
    }
    const start = index;
    const paragraph: string[] = [];
    while (index < lines.length && lines[index].trim() &&
      (index === start || !/^(?:#{1,6}\s|[-*+]\s|\d+[.)]\s)/.test(lines[index].trim()))) {
      paragraph.push(lines[index++]);
    }
    blocks.push(<p key={start}>{inline(paragraph.join("\n"))}</p>);
  }
  return blocks;
}

function ReportValue({value, depth = 0}: {value: unknown; depth?: number}) {
  const decoded = decodeReport(value);
  if (depth > 20) return <p>This section is too deeply nested to display.</p>;
  if (decoded === null || decoded === undefined || decoded === "") return <p className="muted">Not provided.</p>;
  if (typeof decoded === "string") return <>{prose(decoded)}</>;
  if (typeof decoded === "boolean") return <p>{decoded ? "Yes" : "No"}</p>;
  if (typeof decoded === "number") return <p>{String(decoded)}</p>;
  if (Array.isArray(decoded)) return decoded.length
    ? <ul>{decoded.map((item, index) => <li key={index}><ReportValue value={item} depth={depth + 1} /></li>)}</ul>
    : <p className="muted">No items provided.</p>;
  if (typeof decoded === "object") {
    const entries = Object.entries(decoded);
    if (!entries.length) return <p className="muted">No details provided.</p>;
    return <>{entries.map(([key, item]) => {
      const wrapper = ["text", "result", "results", "output", "outputs", "content", "markdown"].includes(key.toLowerCase());
      const Heading = depth > 0 ? "h5" : "h4";
      return <div className="agent-report-field" key={key}>
        {!wrapper && <Heading>{label(key)}</Heading>}
        <ReportValue value={item} depth={depth + 1} />
      </div>;
    })}</>;
  }
  return <p>{String(decoded)}</p>;
}

export default function AgentReport({value}: {value: unknown}) {
  return <div className="agent-report"><ReportValue value={value} /></div>;
}
