import { Suspense } from "react";
import { Clock, ExternalLink } from "lucide-react";
import { fetchPRScores } from "@/lib/api";
import { ScoreBadge } from "@/components/score/ScoreBadge";
import { formatRelativeTime } from "@/lib/utils";
import type { PRScore } from "@/types";

// PRs older than 14 days with no update are considered stale
const STALE_DAYS = 14;

export default function StalePage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <Clock className="w-4 h-4 text-yellow-400" />
        </div>
        <div>
          <h1 className="text-xl font-semibold">Stale PRs</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Pull requests with no activity in {STALE_DAYS}+ days.
          </p>
        </div>
      </div>

      <Suspense fallback={<div className="h-64 rounded-xl bg-card animate-pulse" />}>
        <StaleTable />
      </Suspense>
    </div>
  );
}

async function StaleTable() {
  let scores: PRScore[] = [];

  try {
    scores = await fetchPRScores({ limit: 200 });
  } catch {
    return (
      <div className="rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Could not connect to the Klarity backend.
        </p>
      </div>
    );
  }

  const cutoff = Date.now() - STALE_DAYS * 24 * 60 * 60 * 1000;
  const stale = scores.filter((s) => new Date(s.created_at).getTime() < cutoff);

  if (stale.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-sm text-muted-foreground">No stale pull requests. Nice work!</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/30">
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Score</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Pull Request</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden md:table-cell">Author</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden lg:table-cell">Repository</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Age</th>
          </tr>
        </thead>
        <tbody>
          {stale.map((pr) => (
            <StaleRow key={pr.id} pr={pr} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StaleRow({ pr }: { pr: PRScore }) {
  const prUrl = `https://github.com/${pr.repo_full_name}/pull/${pr.pr_number}`;
  const ageDays = Math.floor(
    (Date.now() - new Date(pr.created_at).getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <tr className="border-b border-border last:border-0 hover:bg-muted/20 transition-colors">
      <td className="px-4 py-3">
        <ScoreBadge score={pr.score} size="sm" />
      </td>
      <td className="px-4 py-3 max-w-xs">
        <a
          href={prUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-start gap-1.5 group"
        >
          <span className="text-foreground group-hover:text-primary transition-colors line-clamp-1">
            {pr.pr_title}
          </span>
          <ExternalLink className="w-3 h-3 text-muted-foreground flex-shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
        </a>
        <span className="text-xs text-muted-foreground">#{pr.pr_number}</span>
      </td>
      <td className="px-4 py-3 hidden md:table-cell">
        <a
          href={`https://github.com/${pr.author_login}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          @{pr.author_login}
        </a>
      </td>
      <td className="px-4 py-3 hidden lg:table-cell">
        <span className="text-xs text-muted-foreground font-mono">{pr.repo_full_name}</span>
      </td>
      <td className="px-4 py-3">
        <span className="inline-flex items-center gap-1 text-xs text-yellow-400">
          <Clock className="w-3 h-3" />
          {ageDays}d
        </span>
      </td>
    </tr>
  );
}
