import { fetchPRScores } from "@/lib/api";
import { TrendingUp, Bot, AlertTriangle, CheckCircle } from "lucide-react";

export async function StatsBar() {
  let scores;
  try {
    scores = await fetchPRScores({ limit: 200 });
  } catch {
    return null;
  }

  const total = scores.length;
  const aiCount = scores.filter((s) => s.is_suspected_ai).length;
  const highQuality = scores.filter((s) => s.score >= 60).length;
  const needsWork = scores.filter((s) => s.score < 40).length;
  const avgScore = total > 0 ? Math.round(scores.reduce((a, b) => a + b.score, 0) / total) : 0;

  const stats = [
    { label: "Total PRs", value: total, icon: TrendingUp, color: "text-blue-400" },
    { label: "Avg Score", value: avgScore, icon: CheckCircle, color: "text-emerald-400" },
    { label: "High Quality", value: highQuality, icon: CheckCircle, color: "text-emerald-400" },
    { label: "Suspected AI", value: aiCount, icon: Bot, color: "text-red-400" },
    { label: "Needs Work", value: needsWork, icon: AlertTriangle, color: "text-orange-400" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
      {stats.map(({ label, value, icon: Icon, color }) => (
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
