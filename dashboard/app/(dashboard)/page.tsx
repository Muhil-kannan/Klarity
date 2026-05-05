import { Suspense } from "react";
import { QueueTable } from "@/components/queue/QueueTable";
import { StatsBar } from "@/components/queue/StatsBar";
import { FilterBar } from "@/components/queue/FilterBar";

export default function QueuePage({
  searchParams,
}: {
  searchParams: { repo?: string; min?: string; max?: string; ai?: string };
}) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">PR Queue</h1>
        <p className="text-sm text-muted-foreground mt-1">
          All scored pull requests, sorted by quality score.
        </p>
      </div>

      <Suspense fallback={<div className="h-20 rounded-xl bg-card animate-pulse" />}>
        <StatsBar />
      </Suspense>

      <FilterBar />

      <Suspense fallback={<TableSkeleton />}>
        <QueueTable
          repo={searchParams.repo}
          minScore={searchParams.min ? Number(searchParams.min) : 0}
          maxScore={searchParams.max ? Number(searchParams.max) : 100}
          suspectedAiOnly={searchParams.ai === "true"}
        />
      </Suspense>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="h-16 border-b border-border animate-pulse bg-muted/20" />
      ))}
    </div>
  );
}
