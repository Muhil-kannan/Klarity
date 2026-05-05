import { fetchPRScores } from "@/lib/api";
import { ScoreBadge } from "@/components/score/ScoreBadge";
import { formatRelativeTime, parseSlopSignals } from "@/lib/utils";
import { Bot, ExternalLink } from "lucide-react";
import type { PRScore } from "@/types";

interface QueueTableProps {
  repo?: string;
  minScore: number;
  maxScore: number;
  suspectedAiOnly?: boolean;
}

export async function QueueTable({ repo, minScore, maxScore, suspectedAiOnly }: QueueTableProps) {
  let scores: PRScore[] = [];

  try {
    scores = await fetchPRScores({ repo, minScore, maxScore, suspectedAiOnly, limit: 100 });
  } catch {
    return (
      <div className="rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Could not connect to the Klarity backend. Make sure it&apos;s running.
        </p>
      </div>
    );
  }

  if (scores.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-sm text-muted-foreground">No pull requests found.</p>
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
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground hidden sm:table-cell">Opened</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Flags</th>
          </tr>
        </thead>
        <tbody>
          {scores.map((pr) => (
            <QueueRow key={pr.id} pr={pr} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function QueueRow({ pr }: { pr: PRScore }) {
  const signals = parseSlopSignals(pr.slop_signals);
  const prUrl = `https://github.com/${pr.repo_full_name}/pull/${pr.pr_number}`;

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
          className="text-muted-foreground hover:text-foreground transition-colors text-xs"
        >
          @{pr.author_login}
        </a>
      </td>
      <td className="px-4 py-3 hidden lg:table-cell">
        <span className="text-xs text-muted-foreground font-mono">{pr.repo_full_name}</span>
      </td>
      <td className="px-4 py-3 hidden sm:table-cell">
        <span className="text-xs text-muted-foreground">{formatRelativeTime(pr.created_at)}</span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1.5">
          {pr.is_suspected_ai && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-red-500/10 border border-red-500/20 text-red-400">
              <Bot className="w-3 h-3" />
              AI
            </span>
          )}
          {signals.includes("no_tests_logic_changed") && (
            <span className="px-1.5 py-0.5 rounded text-xs bg-yellow-500/10 border border-yellow-500/20 text-yellow-400">
              no tests
            </span>
          )}
          {signals.includes("generic_commit_messages") && (
            <span className="px-1.5 py-0.5 rounded text-xs bg-orange-500/10 border border-orange-500/20 text-orange-400">
              bad commits
            </span>
          )}
        </div>
      </td>
    </tr>
  );
}
