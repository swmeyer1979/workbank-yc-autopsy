#!/usr/bin/env bash
# Pull raw YC directory + WORKBank CSVs. Idempotent — skips existing files.
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/raw data/raw/workbank

echo "YC batches W24-F25..."
for b in winter-2024 summer-2024 fall-2024 winter-2025 spring-2025 summer-2025 fall-2025; do
  dest="data/raw/yc_${b}.json"
  if [[ ! -f "$dest" ]]; then
    curl -sf "https://yc-oss.github.io/api/batches/${b}.json" -o "$dest"
    echo "  pulled $b"
  fi
done

echo "WORKBank CSVs..."
BASE="https://huggingface.co/datasets/SALT-NLP/WORKBank/resolve/main"
for f in "worker_data/domain_worker_desires.csv" "expert_ratings/expert_rated_technological_capability.csv" "task_data/task_statement_with_metadata.csv"; do
  fname=$(basename "$f")
  dest="data/raw/workbank/${fname}"
  if [[ ! -f "$dest" ]]; then
    curl -sfL "${BASE}/${f}" -o "$dest"
    echo "  pulled ${fname}"
  fi
done

echo "Done. Next: .venv/bin/python scripts/01_extract_tasks.py"
