import type { PRScore } from "@/types";

const FACTORS: { key: keyof PRScore; label: string; max: number }[] = [
  { key: "linked_issue_score", label: "Linked Issue", max: 15 },
  { key: "tests_score", label: "Tests Changed", max: 20 },
  { key: "description_score", label: "Description Quality", max: 15 },
  { key: "commit_quality_score", label: "Commit Quality", max: 20 },
  { key: "author_history_score", label: "Author History", max: 20 },
  { key: "diff_size_score", label: "Diff Size", max: 10 },
];

interface ScoreBreakdownProps {
  pr: PRScore;
}

export function ScoreBreakdown({ pr }: ScoreBreakdownProps) {
  return (
    <div className="space-y-2">
      {FACTORS.map(({ key, label, max }) => {
        const value = pr[key] as number;
        const pct = Math.round((value / max) * 100);
        return (
          <div key={key} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">{label}</span>
              <span className="font-mono text-foreground">
                {value}/{max}
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full bg-primary/60 transition-all"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
