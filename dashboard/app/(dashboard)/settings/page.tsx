import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-muted border border-border">
          <Settings className="w-4 h-4 text-muted-foreground" />
        </div>
        <div>
          <h1 className="text-xl font-semibold">Settings</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Configure Klarity for your repositories.
          </p>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-6 space-y-4">
        <h2 className="text-sm font-medium">Configuration</h2>
        <p className="text-sm text-muted-foreground">
          Add a <code className="text-xs bg-muted px-1.5 py-0.5 rounded">.klarity.yml</code> file
          to the root of your repository to customize scoring weights, auto-responses, and feature flags.
        </p>
        <a
          href="https://github.com/your-org/klarity/blob/main/.klarity.yml.example"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
        >
          View configuration reference →
        </a>
      </div>

      <div className="rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-muted-foreground text-sm">
          Visual config editor is coming in v0.3.
        </p>
      </div>
    </div>
  );
}
