"""
Sidecar to 02_match_to_workbank.py.

Grounds zone assignment in worker-rated WORKBank data via k-NN rather than LLM inference.
For each extracted task, find top-5 WORKBank tasks by cosine; zone coords = cosine-weighted
mean of neighbors' desire_mean and capability_mean. Apply same median-split rubric.

Rationale (documented, logged as methodology deviation from prereg's primary path):
The LLM-inferred desire distribution for YC product-tasks has median 4.00 vs worker-rated
WORKBank median 3.00 — LLM scores startup pitches, not worker perspectives. k-NN stays
grounded in worker data throughout. Run as robustness check alongside LLM-primary.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

ROOT = Path(__file__).parent.parent
PROC = ROOT / "data/processed"

# Load
ext = pd.read_csv(PROC / "task_extractions.csv")
wb = pd.read_csv(PROC / "workbank_task_zones.csv")
print(f"Extracted tasks: {len(ext)}")
print(f"WORKBank tasks: {len(wb)}")

# Embed
print("Loading embedder...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding WORKBank tasks...")
wb_emb = model.encode(wb["Task"].tolist(), show_progress_bar=True, batch_size=64)
print("Embedding extracted tasks...")
ext_emb = model.encode(ext["task_text"].tolist(), show_progress_bar=True, batch_size=64)

# Cosine
print("Computing cosine similarities...")
sim = cosine_similarity(ext_emb, wb_emb)  # (n_ext, n_wb)

# For each extracted task, top-5 neighbors
K = 5
top_k_idx = np.argsort(-sim, axis=1)[:, :K]
top_k_sim = np.take_along_axis(sim, top_k_idx, axis=1)

# Weighted mean of neighbors' desire_mean, capability_mean
# Weights = cosine similarity (clamped to [0, 1])
wb_desire = wb["desire_mean"].values
wb_capability = wb["capability_mean"].values

w = np.clip(top_k_sim, 0, 1)
w_sum = w.sum(axis=1, keepdims=True)
w_sum[w_sum == 0] = 1

neighbor_desires = wb_desire[top_k_idx]  # (n_ext, K)
neighbor_caps = wb_capability[top_k_idx]

knn_desire = (neighbor_desires * w).sum(axis=1) / w_sum[:, 0]
knn_capability = (neighbor_caps * w).sum(axis=1) / w_sum[:, 0]
mean_top_sim = top_k_sim.mean(axis=1)
max_sim = top_k_sim[:, 0]

# Same median-split rubric as primary task-level (from workbank_task_zones.csv)
# d_med = 3.00, c_med = 3.50
D_MED = 3.00
C_MED = 3.50

def zone(d, c):
    hi_d, hi_c = d >= D_MED, c >= C_MED
    return ["Low-Priority", "Yellow", "Red", "Green"][2 * hi_c + hi_d]

knn_zones = [zone(d, c) for d, c in zip(knn_desire, knn_capability)]

# Build output
out = ext.copy()
out["knn_desire"] = knn_desire
out["knn_capability"] = knn_capability
out["knn_zone"] = knn_zones
out["knn_max_cosine"] = max_sim
out["knn_mean_top5_cosine"] = mean_top_sim

# Top-1 neighbor for interpretability
out["knn_top1_workbank_task_id"] = wb.iloc[top_k_idx[:, 0]]["Task ID"].values
out["knn_top1_workbank_task"] = wb.iloc[top_k_idx[:, 0]]["Task"].values

out.to_csv(PROC / "task_zone_assignments_knn.csv", index=False)
print(f"\nSaved {len(out)} rows to task_zone_assignments_knn.csv")

print("\n=== k-NN ZONE DISTRIBUTION (task-level) ===")
print(out["knn_zone"].value_counts())
print(f"Red+Low-Priority share: {(out['knn_zone'].isin(['Red','Low-Priority'])).mean():.1%}")
print(f"\nMean top-1 cosine: {out['knn_max_cosine'].mean():.3f}")
print(f"Mean top-5 cosine:  {out['knn_mean_top5_cosine'].mean():.3f}")
print(f"\nKNN desire: mean={knn_desire.mean():.2f} median={np.median(knn_desire):.2f}")
print(f"KNN capability: mean={knn_capability.mean():.2f} median={np.median(knn_capability):.2f}")

# Also: compute company-level zone_alignment_score (knn variant)
print("\n=== COMPANY-LEVEL (k-NN) ===")
out["zone_hi_desire"] = out["knn_zone"].isin(["Green", "Yellow"]).astype(int)
comp = out.groupby("slug").apply(
    lambda g: pd.Series({
        "knn_zone_alignment_score": (g["importance"] * g["zone_hi_desire"]).sum() / g["importance"].sum(),
        "knn_mean_desire": (g["importance"] * g["knn_desire"]).sum() / g["importance"].sum(),
        "knn_mean_capability": (g["importance"] * g["knn_capability"]).sum() / g["importance"].sum(),
        "knn_mean_cosine": g["knn_max_cosine"].mean(),
        "n_tasks": len(g),
    }),
    include_groups=False,
).reset_index()

# Zone category (weighted mode with ties → Red/Low)
def weighted_modal_zone(g):
    totals = (g.assign(w=g["importance"]).groupby("knn_zone")["w"].sum()
              .reindex(["Green", "Yellow", "Red", "Low-Priority"], fill_value=0))
    max_val = totals.max()
    top = totals[totals == max_val].index.tolist()
    for z in ["Low-Priority", "Red", "Yellow", "Green"]:
        if z in top:
            return z
    return top[0]

zcat = out.groupby("slug").apply(weighted_modal_zone, include_groups=False)
comp = comp.merge(zcat.rename("knn_zone_category").reset_index(), on="slug")

comp.to_csv(PROC / "company_zone_scores_knn.csv", index=False)
print(comp["knn_zone_category"].value_counts())
print(f"\nsaved company_zone_scores_knn.csv ({len(comp)} rows)")

# Meta
meta_path = PROC / "pipeline_meta.json"
meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
meta["knn_sidecar"] = {
    "k": K,
    "weighting": "cosine_similarity",
    "embedder": "all-MiniLM-L6-v2",
    "desire_median_split": D_MED,
    "capability_median_split": C_MED,
    "rationale": "LLM-inferred desire biased high (median 4.0 vs WORKBank worker 3.0); k-NN grounds in worker data.",
    "task_level_red_low_share": float((out["knn_zone"].isin(["Red", "Low-Priority"])).mean()),
    "company_level_zone_counts": comp["knn_zone_category"].value_counts().to_dict(),
}
meta_path.write_text(json.dumps(meta, indent=2))
print("\nMeta updated.")
