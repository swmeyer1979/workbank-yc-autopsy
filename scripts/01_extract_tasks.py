#!/usr/bin/env python3
"""
01_extract_tasks.py
Extract 3–7 O*NET-style product-tasks per YC company via Sonnet 4.6.
Batches of 50 companies per LLM call. Resume-safe (skips completed batches).
"""

import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from tqdm import tqdm

REPO = Path(__file__).resolve().parent.parent
DATA_IN = REPO / "data" / "processed"
DATA_OUT = REPO / "data" / "processed"
CACHE_DIR = DATA_OUT / "cache" / "01_batches"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

YC_CSV = DATA_IN / "yc_companies.csv"
OUT_CSV = DATA_OUT / "task_extractions.csv"
OUT_JSONL = DATA_OUT / "task_extractions_raw.jsonl"
META_JSON = DATA_OUT / "pipeline_meta.json"

MODEL = "claude-sonnet-4-6"
BATCH_SIZE = 50


def load_companies():
    with open(YC_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def make_prompt(companies_batch):
    """Build the extraction prompt for a batch of companies."""
    examples = json.dumps([
        {
            "slug": "example-co",
            "tasks": [
                {"task_text": "Analyze customer support tickets to identify recurring issues", "importance": 5},
                {"task_text": "Generate automated responses to common customer inquiries", "importance": 4},
                {"task_text": "Route escalated tickets to appropriate human agents", "importance": 3}
            ]
        }
    ], indent=2)

    companies_json = json.dumps([
        {
            "slug": c["slug"],
            "name": c["name"],
            "one_liner": c.get("one_liner", ""),
            "long_description": c.get("long_description", "")
        }
        for c in companies_batch
    ], indent=2)

    return f"""You are extracting product-tasks from startup descriptions for an occupational research study.

For each company below, extract 3–7 primary tasks that the company's product performs or automates, expressed as O*NET-style task statements.

Rules:
- Each task: imperative verb + object, 8–20 words (e.g. "Analyze financial statements to identify cost-reduction opportunities")
- importance 1–5: 5=core product capability, 1=peripheral/supporting
- Focus on what the PRODUCT does, not what the company does as an organization
- Tasks should map to recognizable worker tasks (think: what job function does this replace or assist?)
- Return ONLY a valid JSON array, no prose, no markdown fences

Example output format:
{examples}

Companies to process:
{companies_json}

Return a JSON array with one object per company, each having: "slug" (string), "tasks" (array of objects with "task_text" and "importance").
"""


def call_claude(prompt, slug_list):
    """Call claude CLI, return (parsed_list_or_None, raw_output_str)."""
    result = subprocess.run(
        [
            "claude", "--print",
            "--model", MODEL,
            "--permission-mode", "bypassPermissions",
            "--output-format", "json",
            "-p", prompt
        ],
        capture_output=True, text=True, timeout=300
    )
    raw = result.stdout.strip()
    if result.returncode != 0:
        print(f"  [WARN] claude CLI error: {result.stderr[:200]}", file=sys.stderr)
        return None, raw

    try:
        outer = json.loads(raw)
        reply = outer.get("result", "")
    except json.JSONDecodeError:
        reply = raw

    # Strip markdown fences if model wrapped output
    reply_clean = reply.strip()
    if reply_clean.startswith("```"):
        lines = reply_clean.split("\n")
        # Drop first and last fence lines
        inner = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            if line.startswith("```") and in_block:
                break
            if in_block:
                inner.append(line)
        reply_clean = "\n".join(inner)

    try:
        parsed = json.loads(reply_clean)
        if isinstance(parsed, list):
            return parsed, raw
        return None, raw
    except json.JSONDecodeError:
        return None, raw


def retry_call(companies_batch, batch_idx):
    """Tighter retry prompt — ask for strict JSON only."""
    slugs = [c["slug"] for c in companies_batch]
    tighter = (
        "Return ONLY a JSON array, no other text whatsoever.\n"
        "Each element: {\"slug\": \"...\", \"tasks\": [{\"task_text\": \"...\", \"importance\": N}]}\n"
        "Companies:\n" +
        json.dumps([{"slug": c["slug"], "name": c["name"],
                     "one_liner": c.get("one_liner",""),
                     "long_description": c.get("long_description","")} for c in companies_batch])
    )
    return call_claude(tighter, slugs)


def main():
    companies = load_companies()
    n = len(companies)
    print(f"Loaded {n} companies")

    batches = [companies[i:i+BATCH_SIZE] for i in range(0, n, BATCH_SIZE)]
    print(f"Batches: {len(batches)} × {BATCH_SIZE}")

    all_rows = []
    skipped_slugs = []
    jsonl_entries = []

    for batch_idx, batch in enumerate(tqdm(batches, desc="Extracting tasks")):
        cache_file = CACHE_DIR / f"batch_{batch_idx:04d}.json"
        slug_list = [c["slug"] for c in batch]

        if cache_file.exists():
            with open(cache_file) as f:
                parsed = json.load(f)
        else:
            prompt = make_prompt(batch)
            parsed, raw = call_claude(prompt, slug_list)

            if parsed is None:
                print(f"\n  [WARN] batch {batch_idx} failed, retrying...", file=sys.stderr)
                parsed, raw = retry_call(batch, batch_idx)

            jsonl_entries.append({
                "batch_idx": batch_idx,
                "slugs": slug_list,
                "raw_output": raw,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            if parsed is None:
                print(f"\n  [ERROR] batch {batch_idx} still malformed — skipping slugs: {slug_list}", file=sys.stderr)
                skipped_slugs.extend(slug_list)
                # Write empty cache so we don't retry endlessly on resume
                cache_file.write_text("[]")
                continue

            with open(cache_file, "w") as f:
                json.dump(parsed, f)

        # Build slug→result lookup
        result_map = {}
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and "slug" in item:
                    result_map[item["slug"]] = item

        ts = datetime.now(timezone.utc).isoformat()
        for company in batch:
            slug = company["slug"]
            item = result_map.get(slug)
            if item is None or not item.get("tasks"):
                skipped_slugs.append(slug)
                continue
            for task_idx, t in enumerate(item["tasks"]):
                tt = t.get("task_text", "").strip()
                imp = t.get("importance", 3)
                if not tt:
                    continue
                all_rows.append({
                    "slug": slug,
                    "task_idx": task_idx,
                    "task_text": tt,
                    "importance": int(imp),
                    "batch_idx": batch_idx,
                    "extraction_timestamp": ts
                })

    # Write CSV
    fieldnames = ["slug", "task_idx", "task_text", "importance", "batch_idx", "extraction_timestamp"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nWrote {len(all_rows)} task rows to {OUT_CSV}")

    # Write JSONL (append mode for resume — but deduplicate by batch_idx)
    existing_batches = set()
    if OUT_JSONL.exists():
        with open(OUT_JSONL) as f:
            for line in f:
                try:
                    existing_batches.add(json.loads(line)["batch_idx"])
                except Exception:
                    pass
    with open(OUT_JSONL, "a", encoding="utf-8") as f:
        for entry in jsonl_entries:
            if entry["batch_idx"] not in existing_batches:
                f.write(json.dumps(entry) + "\n")
    print(f"Appended {len(jsonl_entries)} JSONL entries to {OUT_JSONL}")

    # Unique companies with ≥3 tasks
    from collections import Counter
    task_counts = Counter(r["slug"] for r in all_rows)
    ge3 = sum(1 for v in task_counts.values() if v >= 3)
    print(f"Companies with ≥3 tasks: {ge3} / {len(task_counts)}")
    if skipped_slugs:
        print(f"Skipped/malformed slugs ({len(skipped_slugs)}): {skipped_slugs[:10]}{'...' if len(skipped_slugs)>10 else ''}")

    # Update pipeline_meta
    meta = {}
    if META_JSON.exists():
        meta = json.loads(META_JSON.read_text())
    meta["01_extract_tasks"] = {
        "model": MODEL,
        "model_version_note": "claude-sonnet-4-6 via claude CLI; temperature not exposed in CLI",
        "n_companies_input": n,
        "n_task_rows": len(all_rows),
        "n_companies_with_tasks": len(task_counts),
        "n_companies_ge3_tasks": ge3,
        "n_skipped_slugs": len(skipped_slugs),
        "batch_size": BATCH_SIZE,
        "run_timestamp": datetime.now(timezone.utc).isoformat()
    }
    META_JSON.write_text(json.dumps(meta, indent=2))
    print(f"Updated {META_JSON}")


if __name__ == "__main__":
    main()
