export interface PRScore {
  id: number;
  repo_full_name: string;
  pr_number: number;
  pr_title: string;
  author_login: string;
  score: number;
  linked_issue_score: number;
  tests_score: number;
  description_score: number;
  commit_quality_score: number;
  author_history_score: number;
  diff_size_score: number;
  is_suspected_ai: boolean;
  slop_signals: string; // JSON array string
  comment_id: number | null;
  created_at: string;
}

export interface DashboardStats {
  total_prs: number;
  avg_score: number;
  high_quality: number;
  needs_work: number;
  suspected_ai: number;
  repos: number;
}

export interface Contributor {
  author_login: string;
  repo_full_name: string;
  total_prs: number;
  merged_prs: number;
  abandoned_prs: number;
  avg_score: number;
  first_contribution_at: string | null;
  updated_at: string;
}

export interface ScoreBreakdown {
  linked_issue: number;
  tests_changed: number;
  description_quality: number;
  commit_quality: number;
  author_history: number;
  diff_size: number;
}

export type ScoreLabel = "Excellent" | "Good" | "Needs Work" | "Poor" | "Suspected Slop";

export interface DashboardFilters {
  repo?: string;
  minScore: number;
  maxScore: number;
  suspectedAiOnly: boolean;
}
