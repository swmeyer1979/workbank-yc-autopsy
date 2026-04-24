"""
08_rerun_analysis_v2.py — Re-run Fisher's exact tests on shuttered_v2 label.

Reads analysis.csv (after 05_build_analysis_frame.py has been re-run with
shuttered_v2 in place), then recomputes:
  1. Confusion matrix: v1 (single-source) vs v2 (2-of-3)
  2. Fisher's exact: Red vs rest
  3. Fisher's exact: Low-Priority vs rest
  4. Fisher's exact: Red+Low vs Green+Yellow

Writes docs/shuttered_v2_comparison.md
"""

import os
import csv
from collections import Counter

import pandas as pd
import numpy as np
from scipy.stats import fisher_exact

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS = os.path.join(BASE, "data", "processed", "analysis.csv")
DOCS_DIR = os.path.join(BASE, "docs")


def fishers(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    """
    [[a, b],   a=exposed+outcome, b=exposed+no-outcome
     [c, d]]   c=control+outcome, d=control+no-outcome
    Returns (odds_ratio, p_value), one-sided (greater).
    """
    table = [[a, b], [c, d]]
    or_, p = fisher_exact(table, alternative="greater")
    return round(float(or_), 4), round(float(p), 6)


def run_fisher(df: pd.DataFrame, zone_col: str, exposed_vals: list,
               shuttered_col: str = "shuttered_v2") -> dict:
    """
    2×2 for exposed_vals vs rest on shuttered outcome.
    shuttered_col expected values: 'shuttered' | 'live' (ambiguous/no_label excluded).
    """
    usable = df[df[shuttered_col].isin(["shuttered", "live"])].copy()
    usable["exposed"]  = usable[zone_col].isin(exposed_vals)
    usable["outcome"]  = usable[shuttered_col] == "shuttered"

    a = int(usable[ usable.exposed &  usable.outcome].shape[0])  # exposed & shuttered
    b = int(usable[ usable.exposed & ~usable.outcome].shape[0])  # exposed & live
    c = int(usable[~usable.exposed &  usable.outcome].shape[0])  # control & shuttered
    d = int(usable[~usable.exposed & ~usable.outcome].shape[0])  # control & live

    n_exposed  = a + b
    n_control  = c + d
    rate_exp   = a / n_exposed if n_exposed else 0
    rate_ctrl  = c / n_control if n_control else 0

    or_, p = fishers(a, b, c, d)

    return {
        "a": a, "b": b, "c": c, "d": d,
        "n_exposed": n_exposed, "n_control": n_control,
        "rate_exposed": round(rate_exp, 4),
        "rate_control": round(rate_ctrl, 4),
        "odds_ratio": or_,
        "p_one_sided": p,
    }


def main() -> None:
    df = pd.read_csv(ANALYSIS)
    print(f"Loaded analysis.csv: {df.shape}")

    # ── Confusion matrix: v1 vs v2 ────────────────────────────────────────────
    # v1: shuttered_v1_singlesource (bool)
    # v2: shuttered_v2 (live / shuttered / ambiguous / no_label)
    if "shuttered_v1_singlesource" not in df.columns:
        print("ERROR: shuttered_v1_singlesource not in analysis.csv — re-run 05 first")
        return
    if "shuttered_v2" not in df.columns:
        print("ERROR: shuttered_v2 not in analysis.csv — re-run 05 after 07 first")
        return

    df["v1_shuttered"] = df["shuttered_v1_singlesource"].astype(str).map(
        {"True": True, "False": False, "true": True, "false": False}
    )
    v1_total  = int(df["v1_shuttered"].sum())
    v2_counts = df["shuttered_v2"].value_counts().to_dict()

    # Confusion matrix (v1=True rows, what v2 says)
    v1_true_df   = df[df["v1_shuttered"] == True]
    v1_in_v2     = v1_true_df["shuttered_v2"].value_counts().to_dict()
    v2_shuttered = v2_counts.get("shuttered", 0)
    v2_live      = v2_counts.get("live", 0)
    v2_ambig     = v2_counts.get("ambiguous", 0)
    v2_nolabel   = v2_counts.get("no_label", 0)

    flipped_to_live = v1_in_v2.get("live", 0)
    flipped_pct     = round(100 * flipped_to_live / v1_total, 1) if v1_total else 0

    # ── Fisher tests on v2 ────────────────────────────────────────────────────
    zone_col = "zone_category"
    if zone_col not in df.columns:
        # try knn fallback
        zone_col = "zone_category_knn" if "zone_category_knn" in df.columns else None

    tests = {}
    if zone_col:
        tests["red_vs_rest"]         = run_fisher(df, zone_col, ["Red"])
        tests["low_vs_rest"]         = run_fisher(df, zone_col, ["Low-Priority"])
        tests["red_low_vs_green_yel"] = run_fisher(
            df[df[zone_col].isin(["Red","Low-Priority","Green","Yellow"])].copy(),
            zone_col, ["Red", "Low-Priority"],
        )
    else:
        print("WARNING: zone_category column not found — skipping Fisher tests")

    # ── Print summary ─────────────────────────────────────────────────────────
    print(f"\n── Shuttered label comparison ──────────────────────────")
    print(f"  v1 (single-source) shuttered=True: {v1_total}")
    print(f"  v2 shuttered:  {v2_shuttered}")
    print(f"  v2 live:       {v2_live}")
    print(f"  v2 ambiguous:  {v2_ambig}")
    print(f"  v2 no_label:   {v2_nolabel}")
    print(f"\n── Confusion (v1=shuttered → v2 label) ─────────────────")
    for label, n in v1_in_v2.items():
        pct = round(100 * n / v1_total, 1) if v1_total else 0
        print(f"  v1-shuttered → v2-{label}: {n} ({pct}%)")
    print(f"\n  v1-shuttered that flipped to v2-live: {flipped_to_live} ({flipped_pct}%)")

    if tests:
        print(f"\n── Fisher's exact (v2 label, one-sided 'greater') ───────")
        for name, t in tests.items():
            print(f"\n  [{name}]")
            print(f"    exposed ({t['n_exposed']}): shuttered={t['a']}, live={t['b']} "
                  f"  rate={t['rate_exposed']:.1%}")
            print(f"    control ({t['n_control']}): shuttered={t['c']}, live={t['d']} "
                  f"  rate={t['rate_control']:.1%}")
            print(f"    OR={t['odds_ratio']}  p(one-sided)={t['p_one_sided']}")
            sig = "SIGNIFICANT (p<0.05)" if t["p_one_sided"] < 0.05 else "null"
            print(f"    → {sig}")

    # ── Write docs/shuttered_v2_comparison.md ────────────────────────────────
    os.makedirs(DOCS_DIR, exist_ok=True)
    out_path = os.path.join(DOCS_DIR, "shuttered_v2_comparison.md")

    lines = [
        "# Shuttered Label v2 — 2-of-3 Source Comparison",
        "",
        "## Motivation",
        "",
        "Single-source `shuttered` label had ~60% false-positive rate: bot-protection "
        "(Cloudflare etc.) caused HTTP fetch failures for live sites. Spot-check: 3 of 5 "
        "labeled 'shuttered' returned HTTP 200 with full page content. Preregistration "
        "required 2 independent sources; this restores that requirement.",
        "",
        "## Sources",
        "",
        "| Source | Method | Null condition |",
        "|--------|--------|----------------|",
        "| A | Browser-grade fetch (scrapling StealthyFetcher → AsyncFetcher → requests Chrome UA) | fetch error / no URL |",
        "| B | YC self-reported status (Active/Acquired = live; Inactive = shuttered) | missing status |",
        "| C | Wayback Machine last-snapshot recency (≤180 days = live; older/never = shuttered) | never archived |",
        "",
        "## Merge Rule",
        "",
        "- **Live**: ≥2 sources say live",
        "- **Shuttered**: ≥2 sources say shuttered",
        "- **Ambiguous**: 1 live, 1 shuttered, 1 null",
        "- **No-label**: ≥2 sources null",
        "",
        "Confidence: **high** = all 3 non-null agree; **low** = 2 of 3 agree.",
        "",
        "## Label Counts",
        "",
        f"| Label | N |",
        f"|-------|---|",
        f"| v1 shuttered (single-source) | {v1_total} |",
        f"| v2 shuttered (2-of-3) | {v2_shuttered} |",
        f"| v2 live | {v2_live} |",
        f"| v2 ambiguous | {v2_ambig} |",
        f"| v2 no_label | {v2_nolabel} |",
        "",
        "## Confusion Matrix (v1=shuttered → v2 outcome)",
        "",
        "| v2 label | N | % of v1-shuttered |",
        "|----------|---|-------------------|",
    ]

    for label, n in sorted(v1_in_v2.items()):
        pct = round(100 * n / v1_total, 1) if v1_total else 0
        lines.append(f"| {label} | {n} | {pct}% |")

    lines += [
        "",
        f"**v1-shuttered that flipped to v2-live: {flipped_to_live} ({flipped_pct}%)**",
        "",
        "## Fisher's Exact Results (v2 label)",
        "",
    ]

    if tests:
        lines += [
            "| Test | N exposed | Rate exp | N control | Rate ctrl | OR | p (one-sided) | Verdict |",
            "|------|-----------|----------|-----------|-----------|-----|---------------|---------|",
        ]
        for name, t in tests.items():
            sig = "sig" if t["p_one_sided"] < 0.05 else "null"
            lines.append(
                f"| {name} | {t['n_exposed']} | {t['rate_exposed']:.1%} | "
                f"{t['n_control']} | {t['rate_control']:.1%} | "
                f"{t['odds_ratio']} | {t['p_one_sided']} | {sig} |"
            )
    else:
        lines.append("_zone_category not found in analysis.csv — skipped_")

    lines += [
        "",
        "## Headline Finding Status",
        "",
        "_(Fill in manually after inspecting results above)_",
        "",
        "- Red-zone direction reversal finding: [survives / does not survive / attenuated]",
        "- Low-Priority finding: [survives / does not survive / attenuated]",
        "- Red+Low vs Green+Yellow: [survives / does not survive / attenuated]",
        "",
        "---",
        "_Generated by scripts/08_rerun_analysis_v2.py_",
    ]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
