import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../api/client";
import { radarApi } from "../api/radar";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatusBadge,
} from "../components/ui";
import type { CollectionRun, Competitor, Source } from "../types";

type CardData = {
  competitor: Competitor;
  sources: Source[];
  latestRun?: CollectionRun;
};

export function DashboardPage() {
  const [cards, setCards] = useState<CardData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const [showAdd, setShowAdd] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(undefined);
    try {
      const competitors = await radarApi.listCompetitors();
      const data = await Promise.all(
        competitors.map(async (competitor) => {
          const sources = await radarApi.listSources(competitor.id);
          const runs = await Promise.all(
            sources.map((source) => radarApi.listRuns(source.id)),
          );
          const latestRun = runs
            .flat()
            .sort(
              (a, b) =>
                new Date(b.finished_at ?? b.started_at).getTime() -
                new Date(a.finished_at ?? a.started_at).getTime(),
            )[0];
          return { competitor, sources, latestRun };
        }),
      );
      setCards(data);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Could not load competitors.",
      );
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    void load();
  }, []);

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">COMPETITIVE INTELLIGENCE</p>
          <h1>Know what changed before it changes the market.</h1>
          <p className="lead">
            Monitor public competitor data, verify changes, and ask grounded
            questions.
          </p>
        </div>
        <button className="button primary" onClick={() => setShowAdd(true)}>
          + Add competitor
        </button>
      </header>
      <section className="section-header">
        <div>
          <h2>Competitors</h2>
          <p>
            {cards.length
              ? `${cards.length} active monitor${cards.length === 1 ? "" : "s"}`
              : "Your monitoring workspace"}
          </p>
        </div>
      </section>
      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error} onRetry={() => void load()} />
      ) : cards.length === 0 ? (
        <EmptyState
          title="Start monitoring your first competitor"
          detail="Add a public page and tell us what to extract. We’ll turn it into one ready-to-run monitor."
          action={
            <button className="button primary" onClick={() => setShowAdd(true)}>
              + Add competitor
            </button>
          }
        />
      ) : (
        <div className="competitor-grid">
          {cards.map(({ competitor, sources, latestRun }) => (
            <Link
              className="competitor-card"
              to={`/competitors/${competitor.id}`}
              key={competitor.id}
            >
              <div className="card-top">
                <span className="avatar">
                  {competitor.name.slice(0, 1).toUpperCase()}
                </span>
                <span aria-hidden="true">→</span>
              </div>
              <h3>{competitor.name}</h3>
              <p className="url">{new URL(competitor.website_url).host}</p>
              <div className="card-meta">
                <span>
                  {sources.length} source{sources.length === 1 ? "" : "s"}
                </span>
                {latestRun ? (
                  <StatusBadge value={latestRun.health_status} />
                ) : (
                  <span className="status neutral">
                    <span className="dot" />
                    Setup needed
                  </span>
                )}
              </div>
              <p className="last-collected">
                {latestRun?.finished_at
                  ? `Last collected ${formatRelative(latestRun.finished_at)}`
                  : "No collection yet"}
              </p>
            </Link>
          ))}
        </div>
      )}
      <AddCompetitorModal
        open={showAdd}
        onClose={() => setShowAdd(false)}
        onCompleted={() => {
          setShowAdd(false);
          void load();
        }}
      />
    </>
  );
}

function AddCompetitorModal({
  open,
  onClose,
  onCompleted,
}: {
  open: boolean;
  onClose: () => void;
  onCompleted: () => void;
}) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [description, setDescription] = useState("");
  const [stage, setStage] = useState<"form" | "creating" | "ready" | "failed">(
    "form",
  );
  const [competitorId, setCompetitorId] = useState<number>();
  const [sourceId, setSourceId] = useState<number>();
  const [error, setError] = useState("");
  if (!open) return null;
  const create = async (event: FormEvent) => {
    event.preventDefault();
    setStage("creating");
    setError("");
    try {
      const parsed = new URL(url);
      let currentCompetitorId = competitorId;
      if (!currentCompetitorId) {
        const competitor = await radarApi.createCompetitor({
          name,
          website_url: parsed.origin,
        });
        currentCompetitorId = competitor.id;
        setCompetitorId(currentCompetitorId);
      }
      let currentSourceId = sourceId;
      if (!currentSourceId) {
        const source = await radarApi.createSource(currentCompetitorId, {
          name: `${name} - Competitive Monitor`,
          url: parsed.href,
          source_type: "website",
          active: true,
          extraction_description: description,
        });
        currentSourceId = source.id;
        setSourceId(currentSourceId);
      }
      await radarApi.createScraper(currentSourceId);
      setStage("ready");
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "We could not create this monitor.",
      );
      setStage("failed");
    }
  };
  const close = () => {
    if (stage !== "creating") onClose();
  };
  return (
    <div className="modal-backdrop" role="presentation">
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label="Add competitor"
      >
        <button
          className="icon-button"
          onClick={close}
          disabled={stage === "creating"}
          aria-label="Close"
        >
          ×
        </button>
        {stage === "form" || stage === "failed" ? (
          <>
            <p className="eyebrow">NEW MONITOR</p>
            <h2>Add a competitor</h2>
            <p className="modal-lead">
              We’ll configure the source and build its scraper as one simple
              workflow.
            </p>
            {stage === "failed" && <p className="inline-error">{error}</p>}
            <form onSubmit={create}>
              <label>
                Competitor name
                <input
                  required
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Acme Corp"
                />
              </label>
              <label>
                Website or page to monitor
                <input
                  required
                  type="url"
                  value={url}
                  onChange={(event) => setUrl(event.target.value)}
                  placeholder="https://example.com/products"
                />
              </label>
              <label>
                What should we track?
                <textarea
                  required
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="Extract product name, price, availability, product URL, and description."
                  rows={4}
                />
              </label>
              <button className="button primary full" type="submit">
                {stage === "failed" ? "Retry monitor setup" : "Create monitor"}
              </button>
            </form>
          </>
        ) : stage === "creating" ? (
          <Progress />
        ) : (
          <div className="success-state">
            <div className="success-mark">✓</div>
            <p className="eyebrow">MONITOR READY</p>
            <h2>Your competitor monitor is ready.</h2>
            <p>
              Bright Data confirmed the scraper configuration. You can collect
              its first dataset from the workspace.
            </p>
            <div className="modal-actions">
              <Link
                className="button primary"
                to={`/competitors/${competitorId}`}
              >
                View competitor
              </Link>
              <button className="button secondary" onClick={onCompleted}>
                Back to dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Progress() {
  return (
    <div className="progress-state">
      <span className="progress-orb" />
      <p className="eyebrow">PREPARING YOUR MONITOR</p>
      <h2>Creating an AI-powered scraper</h2>
      <p>
        Bright Data is building the collector from your extraction requirements.
        This can take a moment.
      </p>
      <ul className="progress-list">
        <li className="done">
          <span className="step-icon">✓</span>
          <span>Competitor created</span>
        </li>
        <li className="done">
          <span className="step-icon">✓</span>
          <span>Source configured</span>
        </li>
        <li className="active">
          <span className="step-spinner" aria-hidden="true" />
          <span>Building scraper</span>
        </li>
      </ul>
    </div>
  );
}
function formatRelative(timestamp: string) {
  const minutes = Math.max(
    0,
    Math.round((Date.now() - new Date(timestamp).getTime()) / 60000),
  );
  return minutes < 2
    ? "just now"
    : minutes < 60
      ? `${minutes} min ago`
      : `${Math.round(minutes / 60)} hr ago`;
}
