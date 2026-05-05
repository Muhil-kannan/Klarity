"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { Bot, X } from "lucide-react";
import { cn } from "@/lib/utils";

function FilterBarInner() {
  const router = useRouter();
  const params = useSearchParams();

  const aiOnly = params.get("ai") === "true";

  const toggle = useCallback(
    (key: string, value: string) => {
      const next = new URLSearchParams(params.toString());
      if (next.get(key) === value) {
        next.delete(key);
      } else {
        next.set(key, value);
      }
      router.push(`/?${next.toString()}`);
    },
    [params, router]
  );

  const clear = useCallback(() => {
    router.push("/");
  }, [router]);

  const hasFilters = params.toString().length > 0;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <button
        onClick={() => toggle("ai", "true")}
        className={cn(
          "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
          aiOnly
            ? "bg-red-500/10 border-red-500/30 text-red-400"
            : "bg-card border-border text-muted-foreground hover:text-foreground"
        )}
      >
        <Bot className="w-3.5 h-3.5" />
        Suspected AI
      </button>

      <button
        onClick={() => toggle("min", "60")}
        className={cn(
          "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
          params.get("min") === "60"
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
            : "bg-card border-border text-muted-foreground hover:text-foreground"
        )}
      >
        High quality (60+)
      </button>

      <button
        onClick={() => toggle("max", "39")}
        className={cn(
          "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
          params.get("max") === "39"
            ? "bg-orange-500/10 border-orange-500/30 text-orange-400"
            : "bg-card border-border text-muted-foreground hover:text-foreground"
        )}
      >
        Needs work (&lt;40)
      </button>

      {hasFilters && (
        <button
          onClick={clear}
          className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="w-3 h-3" />
          Clear
        </button>
      )}
    </div>
  );
}

export function FilterBar() {
  return (
    <Suspense fallback={<div className="h-9" />}>
      <FilterBarInner />
    </Suspense>
  );
}
