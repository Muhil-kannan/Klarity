import { Users } from "lucide-react";

export default function ContributorsPage() {
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

      <div className="rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-muted-foreground text-sm">
          Contributor reputation tracking is coming in v0.2.
        </p>
      </div>
    </div>
  );
}
