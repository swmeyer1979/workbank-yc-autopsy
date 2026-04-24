#!/usr/bin/env python3
"""
03_company_zone_scores.py
Aggregate task-level zone assignments up to company-level zone metrics.
Resume-safe (overwrites output — no intermediate state needed).
"""

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "processed"

ASSIGNMENTS_CSV = DATA / "task_zone_assignments.csv"
COMPANIES_CSV = DATA / "yc_companies.csv"
OUT_CSV = DATA / "company_zone_scores.csv"
META_JSON = DATA / "pipeline_meta.json"

POSITIVE_ZONES = {"Green", "Yellow"}
ALL_ZONES = {"Green", "Yellow", "Red", "Low-Priority"}

# Zone priority for tie-breaking: ties broken toward Red/Low (biases against thesis per prereg)
ZONE_PRIORITY = {"Red": 0, "Low-Priority": 1, "Yellow": 2, "Green": 3}


def load_assignments():
    with open(ASSIGNMENTS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_companies():
    with open(COMPANIES_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def word_count(company):
    one_liner = company.get("one_liner", "") or ""
    long_desc = company.get("long_description", "") or ""
    return len((one_liner + " " + long_desc).split())


def modal_zone_weighted(zone_importance_pairs):
    """
    Importance-weighted modal zone. Ties broken toward Red/Low (lowest ZONE_PRIORITY value).
    """
    totals = defaultdict(float)
    for zone, imp in zone_importance_pairs:
        totals[zone] += float(imp)

    if not totals:
        return "Low-Priority"

    max_weight = max(totals.values())
    candidates = [z for z, w in totals.items() if w == max_weight]

    # Ties: pick the one with lowest priority score (Red < Low-Priority < Yellow < Green)
    return min(candidates, key=lambda z: ZONE_PRIORITY.get(z, -1))


def main():
    assignments = load_assignments()
    companies = load_companies()

    # Index companies by slug for word count + lookup
    company_map = {c["slug"]: c for c in companies}

    # Group assignments by slug
    by_slug = defaultdict(list)
    for row in assignments:
        by_slug[row["slug"]].append(row)

    output_rows = []
    for company in companies:
        slug = company["slug"]
        tasks = by_slug.get(slug, [])
        n_tasks = len(tasks)

        wc = word_count(company)
        low_signal = wc < 50 or n_tasks < 3

        if n_tasks == 0:
            output_rows.append({
                "slug": slug,
                "zone_alignment_score": None,
                "zone_category": None,
                "zone_source_mix": None,
                "n_tasks": 0,
                "mean_importance": None,
                "mean_cosine": None,
                "low_signal": True
            })
            continue

        importances = [float(t["importance"]) for t in tasks]
        zones = [t["zone"] for t in tasks]
        sources = [t["match_source"] for t in tasks]
        cosines = [
            float(t["cosine_similarity"])
            for t in tasks
            if t["match_source"] == "matched" and t["cosine_similarity"] not in ("", None)
        ]

        # zone_alignment_score: importance-weighted fraction in Green+Yellow
        total_imp = sum(importances)
        if total_imp == 0:
            alignment = 0.0
        else:
            alignment = sum(
                imp for imp, zone in zip(importances, zones) if zone in POSITIVE_ZONES
            ) / total_imp

        # zone_category: importance-weighted modal zone, ties toward Red/Low
        zone_category = modal_zone_weighted(list(zip(zones, importances)))

        # zone_source_mix
        source_set = set(sources)
        if source_set == {"matched"}:
            source_mix = "all_matched"
        elif source_set == {"inferred"}:
            source_mix = "all_inferred"
        else:
            source_mix = "mixed"

        output_rows.append({
            "slug": slug,
            "zone_alignment_score": round(alignment, 6),
            "zone_category": zone_category,
            "zone_source_mix": source_mix,
            "n_tasks": n_tasks,
            "mean_importance": round(sum(importances) / len(importances), 4),
            "mean_cosine": round(sum(cosines) / len(cosines), 4) if cosines else None,
            "low_signal": low_signal
        })

    fieldnames = [
        "slug", "zone_alignment_score", "zone_category", "zone_source_mix",
        "n_tasks", "mean_importance", "mean_cosine", "low_signal"
    ]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {len(output_rows)} rows to {OUT_CSV}")

    # Summary stats
    scored = [r for r in output_rows if r["zone_alignment_score"] is not None]
    scores = [r["zone_alignment_score"] for r in scored]
    zone_dist = Counter(r["zone_category"] for r in scored if r["zone_category"])
    low_signal_n = sum(1 for r in output_rows if r["low_signal"])
    source_dist = Counter(r["zone_source_mix"] for r in scored)

    print(f"\nScored companies: {len(scored)} / {len(output_rows)}")
    print(f"Low-signal: {low_signal_n}")
    print(f"zone_alignment_score range: [{min(scores):.3f}, {max(scores):.3f}]")
    print(f"Company-level zone distribution: {dict(zone_dist)}")
    print(f"Source mix: {dict(source_dist)}")

    # Update pipeline meta
    meta = {}
    if META_JSON.exists():
        meta = json.loads(META_JSON.read_text())
    meta["03_company_zone_scores"] = {
        "n_companies_input": len(companies),
        "n_companies_scored": len(scored),
        "n_low_signal": low_signal_n,
        "zone_alignment_score_min": round(min(scores), 4) if scores else None,
        "zone_alignment_score_max": round(max(scores), 4) if scores else None,
        "zone_alignment_score_mean": round(sum(scores) / len(scores), 4) if scores else None,
        "company_zone_distribution": dict(zone_dist),
        "source_mix_distribution": dict(source_dist),
        "run_timestamp": datetime.now(timezone.utc).isoformat()
    }
    META_JSON.write_text(json.dumps(meta, indent=2))
    print(f"Updated {META_JSON}")


if __name__ == "__main__":
    main()
