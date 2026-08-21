import type { PropsWithChildren, ReactNode } from "react";
import { Link } from "react-router-dom";
import type { AgentEvidence, Change, Insight, JsonValue } from "../types";

export function StatusBadge({ value }: { value: string }) {
  const tone = value === "healthy" || value === "succeeded" ? "success" : value === "failed" ? "danger" : value === "degraded" ? "warning" : "neutral";
  return <span className={`status ${tone}`}><span className="dot" />{value}</span>;
}

export function LoadingState({ label = "Loading your competitive intelligence…" }: { label?: string }) {
  return <div className="state loading"><span className="spinner" />{label}</div>;
}

export function EmptyState({ title, detail, action }: { title: string; detail: string; action?: ReactNode }) {
  return <div className="state empty"><div className="empty-mark">⌁</div><h3>{title}</h3><p>{detail}</p>{action}</div>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <div className="state error"><h3>Something needs attention</h3><p>{message}</p>{onRetry && <button className="button secondary" onClick={onRetry}>Try again</button>}</div>;
}

export function Shell({ children }: PropsWithChildren) {
  return <div className="app-shell">
    <aside className="sidebar">
      <Link className="brand" to="/"><span className="brand-mark">◉</span><span>Competitive<br /><strong>AI Radar</strong></span></Link>
      <nav><Link to="/" className="nav-link">Overview</Link><Link to="/" className="nav-link">Competitors</Link></nav>
      <p className="sidebar-note">Evidence-backed intelligence from your collected data.</p>
    </aside>
    <main className="main-content">{children}</main>
  </div>;
}

export function EvidenceList({ evidence }: { evidence: AgentEvidence[] | { source_url: string; reason: string }[] }) {
  if (!evidence.length) return null;
  return <div className="evidence-list"><p className="eyebrow">Evidence</p>{evidence.map((item, index) => <a className="evidence-card" key={`${item.source_url}-${index}`} href={item.source_url} target="_blank" rel="noreferrer"><span><strong>{"source_name" in item ? item.source_name : "Collected source"}</strong><small>{item.reason}</small></span><span aria-hidden="true">↗</span></a>)}</div>;
}

export function JsonData({ value }: { value: JsonValue }) {
  if (Array.isArray(value) && value.length && value.every((item) => typeof item === "object" && item !== null && !Array.isArray(item))) {
    const rows = value as Record<string, JsonValue>[];
    const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))].slice(0, 8);
    return <div className="table-wrap"><table><thead><tr>{columns.map((column) => <th key={column}>{formatLabel(column)}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{columns.map((column) => <td key={column}>{renderValue(row[column])}</td>)}</tr>)}</tbody></table></div>;
  }
  return <pre className="json-view">{JSON.stringify(value, null, 2)}</pre>;
}

export function ChangeCard({ change, insight, onAnalyze, analyzing }: { change: Change; insight?: Insight; onAnalyze: () => void; analyzing: boolean }) {
  const diff = change.diff_data as Record<string, JsonValue>;
  const modified = Array.isArray(diff.modified) ? diff.modified : [];
  return <article className="change-card"><div className="change-header"><div><span className={`change-type ${change.change_type}`}>{change.change_type}</span><h3>{change.summary}</h3></div><span className={`significance ${change.significance}`}>{change.significance} impact</span></div>
    {modified.length > 0 && <div className="change-details">{modified.map((entry, index) => { const item = entry as Record<string, JsonValue>; return <div key={index}><strong>{String(item.record_key ?? "Updated record")}</strong><p>Changed: {Array.isArray(item.changed_fields) ? item.changed_fields.join(", ") : "fields updated"}</p>{item.before !== undefined && item.after !== undefined && <div className="before-after"><pre>{JSON.stringify(item.before, null, 2)}</pre><span>→</span><pre>{JSON.stringify(item.after, null, 2)}</pre></div>}</div>; })}</div>}
    {insight ? <div className="insight-inline"><p className="eyebrow">AI insight</p><h4>{insight.title}</h4><p>{insight.analysis}</p><p><strong>Recommendation:</strong> {insight.recommendation}</p><EvidenceList evidence={insight.evidence} /></div> : ["added", "removed", "modified"].includes(change.change_type) && <button className="button text" onClick={onAnalyze} disabled={analyzing}>{analyzing ? "Analyzing…" : "Generate AI insight"}</button>}
  </article>;
}

function renderValue(value: JsonValue | undefined) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
function formatLabel(value: string) { return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase()); }
