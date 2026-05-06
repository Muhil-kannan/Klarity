import { fetchStats } from "@/lib/api";
import { TrendingUp, Bot, AlertTriangle, CheckCircle, GitBranch } from "lucide-react";

export async function StatsBar({ repo }: { repo?: string }) {
  let stats;
  try {
    stats = await fetchStats(repo);
  } catch {
    return null;
  }

  const items = [
    { label: "Total PRs",     value: stats.total_prs,   icon: TrendingUp,   color: "text-blue-400" },
    { label: "Avg Score",     value: stats.avg_score,   icon: CheckCircle,  color: "text-emerald-400" },
    { label: "High Quality",  value: stats.high_quality, icon: CheckCircle, color: "text-emerald-400" },
    { label: "Suspected AI",  value: stats.suspected_ai, icon: Bot,         color: "text-red-400" },
    { label: "Needs Work",    value: stats.needs_work,  icon: AlertTriangle, color: "text-orange-400" },
    { label: "Repos",         value: stats.repos,       icon: GitBranch,    color: "text-purple-400" },
  ];

  return (
    <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
      {items.map(({ label, value, icon: Icon, color }) => (
        <div key={label} className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-1">
            <Icon className={`w-3.5 h-3.5 ${color}`} />
            <span className="text-xs text-muted-foreground">{label}</span>
          </div>
          <p className="text-2xl font-semibold">{value}</p>
        </div>
      ))}
    </div>
  );
}
