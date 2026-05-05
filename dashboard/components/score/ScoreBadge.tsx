import { cn, getScoreColor, getScoreBgColor, getScoreLabel } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

export function ScoreBadge({ score, size = "md", showLabel = false }: ScoreBadgeProps) {
  const label = getScoreLabel(score);

  return (
    <div className="flex items-center gap-2">
      <span
        className={cn(
          "inline-flex items-center justify-center font-mono font-semibold rounded-lg border",
          getScoreBgColor(score),
          getScoreColor(score),
          size === "sm" && "text-xs px-2 py-0.5",
          size === "md" && "text-sm px-2.5 py-1",
          size === "lg" && "text-lg px-3 py-1.5"
        )}
      >
        {score}
      </span>
      {showLabel && (
        <span className={cn("text-xs font-medium", getScoreColor(score))}>{label}</span>
      )}
    </div>
  );
}
