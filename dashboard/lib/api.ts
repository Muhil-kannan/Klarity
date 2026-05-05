import type { PRScore } from "@/types";

// Server-side: call backend directly. Client-side: use the rewrite proxy.
function getBaseUrl() {
  if (typeof window === "undefined") {
    // Running on the server (Next.js SSR / Server Components)
    return process.env.BACKEND_URL ?? "http://localhost:8000";
  }
  // Running in the browser — use the Next.js rewrite proxy
  return "";
}

async function apiFetch(path: string): Promise<Response> {
  const base = getBaseUrl();
  const url = base
    ? `${base}/api/v1${path}`
    : `/api/backend${path}`;
  return fetch(url, { cache: "no-store" });
}

export async function fetchPRScores(params: {
  repo?: string;
  minScore?: number;
  maxScore?: number;
  suspectedAiOnly?: boolean;
  limit?: number;
  offset?: number;
}): Promise<PRScore[]> {
  const query = new URLSearchParams();
  if (params.repo) query.set("repo", params.repo);
  if (params.minScore !== undefined) query.set("min_score", String(params.minScore));
  if (params.maxScore !== undefined) query.set("max_score", String(params.maxScore));
  if (params.suspectedAiOnly) query.set("suspected_ai_only", "true");
  if (params.limit) query.set("limit", String(params.limit));
  if (params.offset) query.set("offset", String(params.offset));

  const res = await apiFetch(`/dashboard/scores?${query}`);
  if (!res.ok) throw new Error("Failed to fetch PR scores");
  return res.json();
}

export async function fetchPRScore(repoFullName: string, prNumber: number): Promise<PRScore> {
  const res = await apiFetch(`/dashboard/scores/${repoFullName}/${prNumber}`);
  if (!res.ok) throw new Error("Score not found");
  return res.json();
}

export async function checkHealth(): Promise<{ status: string; version: string }> {
  const res = await apiFetch("/health");
  if (!res.ok) throw new Error("Backend unreachable");
  return res.json();
}
