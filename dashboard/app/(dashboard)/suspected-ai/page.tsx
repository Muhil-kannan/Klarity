import { Suspense } from "react";
import { QueueTable } from "@/components/queue/QueueTable";
import { Bot } from "lucide-react";

export default function SuspectedAIPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-red-500/10 border border-red-500/20">
          <Bot className="w-4 h-4 text-red-400" />
        </div>
        <div>
          <h1 className="text-xl font-semibold">Suspected AI PRs</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Pull requests flagged for AI generation signals.
          </p>
        </div>
      </div>

      <Suspense fallback={<div className="h-64 rounded-xl bg-card animate-pulse" />}>
        <QueueTable suspectedAiOnly={true} minScore={0} maxScore={100} />
      </Suspense>
    </div>
  );
}
