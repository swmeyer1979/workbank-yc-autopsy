export type ZoneCategory = 'Green' | 'Yellow' | 'Red' | 'Low-Priority' | 'Unknown';

export interface Company {
  slug: string;
  name: string | null;
  batch: string | null;
  website: string | null;
  one_liner: string | null;
  team_size: number | null;
  is_ai: boolean;
  cohort_months: number | null;
  zone_alignment_score: number | null;
  zone_category: ZoneCategory | null;
  n_tasks: number | null;
}

export interface Summary {
  total: number;
  zone_counts: Record<string, number>;
  batches: string[];
  shutdown_stats_aggregate?: {
    live: number;
    shuttered: number;
    ambiguous: number;
    no_label: number;
  };
  note?: string;
}
