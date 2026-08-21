import { request } from "./client";
import type { AgentAnswer, Change, CollectionRun, Competitor, Insight, Snapshot, Source } from "../types";

export const radarApi = {
  listCompetitors: () => request<Competitor[]>("/competitors"),
  getCompetitor: (id: number) => request<Competitor>(`/competitors/${id}`),
  createCompetitor: (payload: Pick<Competitor, "name" | "website_url"> & Partial<Pick<Competitor, "description" | "active">>) =>
    request<Competitor>("/competitors", { method: "POST", body: JSON.stringify(payload) }),
  listSources: (competitorId: number) => request<Source[]>(`/competitors/${competitorId}/sources`),
  createSource: (competitorId: number, payload: Omit<Source, "id" | "competitor_id" | "collector_id">) =>
    request<Source>(`/competitors/${competitorId}/sources`, { method: "POST", body: JSON.stringify(payload) }),
  createScraper: (sourceId: number) => request<{ collector_id: string; status: string }>(`/sources/${sourceId}/scraper`, { method: "POST" }),
  collectSource: (sourceId: number) => request<CollectionRun>(`/sources/${sourceId}/collect`, { method: "POST" }),
  listRuns: (sourceId: number) => request<CollectionRun[]>(`/sources/${sourceId}/runs`),
  listSnapshots: (sourceId: number) => request<Snapshot[]>(`/sources/${sourceId}/snapshots`),
  listChanges: (sourceId: number) => request<Change[]>(`/sources/${sourceId}/changes`),
  listInsights: (competitorId: number) => request<Insight[]>(`/competitors/${competitorId}/insights`),
  analyzeChange: (changeId: number) => request<Insight>(`/changes/${changeId}/analyze`, { method: "POST" }),
  askCompetitor: (competitorId: number, question: string) =>
    request<AgentAnswer>(`/competitors/${competitorId}/ask`, { method: "POST", body: JSON.stringify({ question }) }),
};
