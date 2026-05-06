import { Suspense } from "react";
import { Users, ExternalLink } from "lucide-react";
import { fetchContributors } from "@/lib/api";
import type { Contributor } from "@/types";
import { formatRelativeTime } from "@/lib/utils";

export default function ContributorsPage({
  searchParams,
}: {
  searchParams: { repo?: string };
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/20">
          <Users className="w-4 h-4 text-blue-400" />
        </div>
        <div>
          <h1 className="text-xl font-semibold">Contributors</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Reputation and history for all contributors.
          </p>
        </div>
      </div>

      <Suspense fallback={<div className="h-64 rounded-xl bg-card animate-pulse" />}>
        <ContributorsTable repo={searchParams.repo} />
      </Suspense>
    </div>
  );
}

async function ContributorsTable({ repo }: { repo?: string }) {
  let contributors: Contributor[] = [];

  try {
    contributors = await fetchContributors({ repo, limit: 100 });
  } catch {
    return (
      <div className="rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Could not connect to the Klarity backend.
        </p>
      </div>
    );
  }

  if (contributors.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-sm text-muted-foreground">
          No contributor data yet. Scores will appear after PRs are analyzed.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/30">
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Contributor</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden lg:table-cell">Repository</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Avg Score</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden sm:table-cell">Total PRs</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden md:table-cell">Merged</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden md:table-cell">Abandoned</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden sm:table-cell">First Seen</th>
          </tr>
        </thead>
        <tbody>
          {contributors.map((c) => (
            <ContributorRow key={`${c.repo_full_name}:${c.author_login}`} contributor={c} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ContributorRow({ contributor: c }: { contributor: Contributor }) {
  const scoreColor =
    c.avg_score >= 60 ? "text-emerald-400" :
    c.avg_score >= 40 ? "text-yellow-400" :
    "text-red-400";

  return (
    <tr className="border-b border-border last:border-0 hover:bg-muted/20 transition-colors">
      <td className="px-4 py-3">
        <a
          href={`https://github.com/${c.author_login}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 group"
        >
          <span className="text-foreground group-hover:text-primary transition-colors">
            @{c.author_login}
          </span>
          <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </a>
      </td>
      <td className="px-4 py-3 hidden lg:table-cell">
        <span className="text-xs text-muted-foreground font-mono">{c.repo_full_name}</span>
      </td>
      <td className="px-4 py-3">
        <span className={`font-semibold ${scoreColor}`}>{c.avg_score}</span>
      </td>
      <td className="px-4 py-3 hidden sm:table-cell">
        <span className="text-muted-foreground">{c.total_prs}</span>
      </td>
      <td className="px-4 py-3 hidden md:table-cell">
        <span className="text-emerald-400">{c.merged_prs}</span>
      </td>
      <td className="px-4 py-3 hidden md:table-cell">
        <span className={c.abandoned_prs > 0 ? "text-orange-400" : "text-muted-foreground"}>
          {c.abandoned_prs}
        </span>
      </td>
      <td className="px-4 py-3 hidden sm:table-cell">
        <span className="text-xs text-muted-foreground">
          {c.first_contribution_at ? formatRelativeTime(c.first_contribution_at) : "—"}
        </span>
      </td>
    </tr>
  );
}
