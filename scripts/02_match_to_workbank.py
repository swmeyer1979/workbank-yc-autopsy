#!/usr/bin/env python3
"""
02_match_to_workbank.py
Embed extracted tasks + WORKBank tasks; match via cosine similarity.
Unmatched tasks (cosine < 0.70) → Sonnet 4.6 for desire/capability scoring.
Resume-safe.
"""

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from tqdm import tqdm

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "processed"
CACHE_DIR = DATA / "cache" / "02_inferred"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

EXTRACTIONS_CSV = DATA / "task_extractions.csv"
WORKBANK_CSV = DATA / "workbank_task_zones.csv"
OUT_CSV = DATA / "task_zone_assignments.csv"
META_JSON = DATA / "pipeline_meta.json"

MODEL = "claude-sonnet-4-6"
COSINE_THRESHOLD = 0.70
BATCH_SIZE = 50

# WORKBank zone medians (fixed from prereg)
DESIRE_MEDIAN = 3.00
CAPABILITY_MEDIAN = 3.50


def ensure_sentence_transformers():
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        print("Installing sentence-transformers...")
        subprocess.run(
            [str(REPO / ".venv" / "bin" / "pip"), "install", "sentence-transformers"],
            check=True
        )


def load_extractions():
    with open(EXTRACTIONS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_workbank():
    with open(WORKBANK_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def embed_texts(model, texts, desc="Embedding"):
    """Embed a list of texts in one shot (sentence-transformers handles batching)."""
    return model.encode(texts, show_progress_bar=True, batch_size=64, convert_to_numpy=True)


def cosine_sim_matrix(a, b):
    """a: (n, d), b: (m, d) → (n, m) cosine similarities."""
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-10)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return a_norm @ b_norm.T


def assign_zone(desire, capability):
    """Apply WORKBank median split."""
    d_high = float(desire) >= DESIRE_MEDIAN
    c_high = float(capability) >= CAPABILITY_MEDIAN
    if d_high and c_high:
        return "Green"
    elif d_high and not c_high:
        return "Yellow"
    elif not d_high and c_high:
        return "Red"
    else:
        return "Low-Priority"


def make_inference_prompt(tasks_batch):
    """Prompt for scoring unmatched tasks with desire + capability."""
    task_list = json.dumps([
        {"task_id": i, "task_text": t["task_text"]}
        for i, t in enumerate(tasks_batch)
    ], indent=2)

    return f"""You are scoring work tasks on two dimensions for an occupational research study.

For each task below, score:
- "desire": How much would workers want this task automated? (1=strongly prefer to keep doing it themselves, 5=strongly want it automated)
- "capability": How capable is current AI at performing this task end-to-end without human oversight? (1=AI cannot do this, 5=AI can fully automate this today)

Use the midpoints of the scales:
- desire 1: workers strongly value doing this / it requires human judgment/creativity
- desire 3: neutral / mixed worker preferences
- desire 5: workers find this tedious / repetitive / would welcome automation
- capability 1: requires physical presence, complex judgment, or skills AI lacks
- capability 3.5: AI can assist but not fully automate
- capability 5: AI can fully perform this today (e.g., text generation, data classification, search)

Return ONLY a valid JSON array, one object per task, with: "task_id" (int, echo back), "desire" (float 1–5), "capability" (float 1–5).

Tasks:
{task_list}
"""


def call_claude_inference(prompt):
    """Call claude CLI for inference scoring. Returns (parsed_list_or_None, raw_str)."""
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
        return None, raw

    try:
        outer = json.loads(raw)
        reply = outer.get("result", "")
    except json.JSONDecodeError:
        reply = raw

    reply_clean = reply.strip()
    if reply_clean.startswith("```"):
        lines = reply_clean.split("\n")
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


def main():
    ensure_sentence_transformers()
    from sentence_transformers import SentenceTransformer

    extractions = load_extractions()
    workbank = load_workbank()
    print(f"Extracted tasks: {len(extractions)}, WORKBank tasks: {len(workbank)}")

    # Build WORKBank lookup
    wb_texts = [r["Task"] for r in workbank]
    wb_ids = [r["Task ID"] for r in workbank]
    wb_map = {r["Task ID"]: r for r in workbank}

    print("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Embedding WORKBank tasks...")
    wb_embeddings = embed_texts(model, wb_texts, "WORKBank")

    print("Embedding extracted tasks...")
    ext_texts = [r["task_text"] for r in extractions]
    ext_embeddings = embed_texts(model, ext_texts, "Extracted")

    print("Computing cosine similarities...")
    # Process in chunks to avoid OOM on large matrices
    CHUNK = 500
    best_scores = []
    best_idxs = []
    for i in range(0, len(ext_embeddings), CHUNK):
        chunk = ext_embeddings[i:i+CHUNK]
        sims = cosine_sim_matrix(chunk, wb_embeddings)  # (chunk_size, 844)
        best_scores.extend(sims.max(axis=1).tolist())
        best_idxs.extend(sims.argmax(axis=1).tolist())

    # Partition into matched vs inferred
    matched_rows = []
    inferred_tasks = []  # list of (extraction_row_idx, extraction_row)

    for i, (row, score, wb_idx) in enumerate(zip(extractions, best_scores, best_idxs)):
        if score >= COSINE_THRESHOLD:
            wb_task = workbank[wb_idx]
            matched_rows.append({
                "slug": row["slug"],
                "task_idx": row["task_idx"],
                "task_text": row["task_text"],
                "importance": row["importance"],
                "match_source": "matched",
                "matched_workbank_task_id": wb_task["Task ID"],
                "matched_workbank_task": wb_task["Task"],
                "cosine_similarity": round(score, 4),
                "desire_mean": wb_task["desire_mean"],
                "capability_mean": wb_task["capability_mean"],
                "zone": wb_task["zone"]
            })
        else:
            inferred_tasks.append((i, row, round(score, 4), workbank[wb_idx]["Task ID"]))

    print(f"Matched: {len(matched_rows)} | Inferred needed: {len(inferred_tasks)}")
    match_rate = len(matched_rows) / max(len(extractions), 1) * 100
    print(f"Match rate: {match_rate:.1f}%")

    # Score inferred tasks via LLM, batched
    inferred_rows = []
    infer_batches = [inferred_tasks[i:i+BATCH_SIZE] for i in range(0, len(inferred_tasks), BATCH_SIZE)]
    print(f"Scoring {len(inferred_tasks)} inferred tasks in {len(infer_batches)} batches...")

    for b_idx, batch in enumerate(tqdm(infer_batches, desc="Inferring zones")):
        cache_file = CACHE_DIR / f"infer_{b_idx:04d}.json"

        if cache_file.exists():
            scored = json.load(open(cache_file))
        else:
            prompt = make_inference_prompt([r for (_, r, _, _) in batch])
            scored, raw = call_claude_inference(prompt)

            if scored is None:
                # Retry once with tighter prompt
                tighter = (
                    "Return ONLY a JSON array. Each element: "
                    "{\"task_id\": N, \"desire\": X.X, \"capability\": X.X}\n"
                    "Tasks:\n" +
                    json.dumps([{"task_id": i, "task_text": r["task_text"]}
                                for i, (_, r, _, _) in enumerate(batch)])
                )
                scored, raw = call_claude_inference(tighter)

            if scored is None:
                print(f"\n  [ERROR] infer batch {b_idx} malformed — assigning zone=Low-Priority fallback",
                      file=sys.stderr)
                scored = [{"task_id": i, "desire": 2.0, "capability": 2.0}
                           for i in range(len(batch))]

            cache_file.write_text(json.dumps(scored))

        # Build task_id → score map
        score_map = {}
        if isinstance(scored, list):
            for s in scored:
                if isinstance(s, dict) and "task_id" in s:
                    score_map[int(s["task_id"])] = s

        for local_i, (ext_i, row, cos_score, near_wb_id) in enumerate(batch):
            s = score_map.get(local_i, {"desire": 2.0, "capability": 2.0})
            desire = float(s.get("desire", 2.0))
            capability = float(s.get("capability", 2.0))
            zone = assign_zone(desire, capability)
            inferred_rows.append({
                "slug": row["slug"],
                "task_idx": row["task_idx"],
                "task_text": row["task_text"],
                "importance": row["importance"],
                "match_source": "inferred",
                "matched_workbank_task_id": near_wb_id,  # nearest even if below threshold
                "matched_workbank_task": "",
                "cosine_similarity": cos_score,
                "desire_mean": round(desire, 4),
                "capability_mean": round(capability, 4),
                "zone": zone
            })

    all_rows = matched_rows + inferred_rows

    # Sort by slug, task_idx
    all_rows.sort(key=lambda r: (r["slug"], int(r["task_idx"])))

    fieldnames = [
        "slug", "task_idx", "task_text", "importance",
        "match_source", "matched_workbank_task_id", "matched_workbank_task",
        "cosine_similarity", "desire_mean", "capability_mean", "zone"
    ]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nWrote {len(all_rows)} rows to {OUT_CSV}")

    # Zone distribution
    from collections import Counter
    zone_dist = Counter(r["zone"] for r in all_rows)
    print("Task-level zone distribution:", dict(zone_dist))

    # Update pipeline meta
    meta = {}
    if META_JSON.exists():
        meta = json.loads(META_JSON.read_text())
    meta["02_match_to_workbank"] = {
        "model": MODEL,
        "model_version_note": "claude-sonnet-4-6 via claude CLI; temperature not exposed in CLI",
        "cosine_threshold": COSINE_THRESHOLD,
        "embedding_model": "all-MiniLM-L6-v2",
        "n_extracted_tasks": len(extractions),
        "n_workbank_tasks": len(workbank),
        "n_matched": len(matched_rows),
        "n_inferred": len(inferred_rows),
        "match_rate_pct": round(match_rate, 2),
        "task_zone_distribution": dict(zone_dist),
        "run_timestamp": datetime.now(timezone.utc).isoformat()
    }
    META_JSON.write_text(json.dumps(meta, indent=2))
    print(f"Updated {META_JSON}")


if __name__ == "__main__":
    main()
