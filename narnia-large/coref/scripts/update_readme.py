"""
Update the results tables in README.md from results/summary.csv.

Run after scoring one or more models:
    python coref/scripts/update_readme.py
"""

import os
import csv

HERE      = os.path.dirname(os.path.abspath(__file__))
COREF_DIR = os.path.dirname(HERE)
RES_DIR   = os.path.join(COREF_DIR, "results")
README    = os.path.join(COREF_DIR, "README.md")
SUMMARY   = os.path.join(RES_DIR, "summary.csv")

RESULTS_START    = "<!-- results:start -->"
RESULTS_END      = "<!-- results:end -->"
RESULTS_FS_START = "<!-- results-fewshot:start -->"
RESULTS_FS_END   = "<!-- results-fewshot:end -->"


def load_summary():
    if not os.path.exists(SUMMARY):
        print(f"No summary file found at {SUMMARY} — run score_baseline.py first.")
        return []
    with open(SUMMARY, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_table(rows, start_marker, end_marker):
    lines = [
        start_marker,
        "| Model | Precision | Recall | F1 |",
        "| ----- | --------- | ------ | -- |",
    ]
    for row in rows:
        lines.append(f"| {row.get('model', '')} | {row.get('precision', '')} | {row.get('recall', '')} | {row.get('f1', '')} |")
    lines.append(end_marker)
    return "\n".join(lines)


def replace_block(content, start_marker, end_marker, new_block):
    start_idx = content.find(start_marker)
    end_idx   = content.find(end_marker)
    if start_idx == -1 or end_idx == -1:
        print(f"Could not find markers {start_marker!r} / {end_marker!r} in README.md.")
        return content
    return content[:start_idx] + new_block + content[end_idx + len(end_marker):]


def update_readme(rows):
    zeroshot = [r for r in rows if not r.get("model", "").endswith("_fewshot")]
    fewshot  = [r for r in rows if r.get("model", "").endswith("_fewshot")]

    with open(README, encoding="utf-8") as f:
        content = f.read()

    content = replace_block(content, RESULTS_START, RESULTS_END,
                             build_table(zeroshot, RESULTS_START, RESULTS_END))
    content = replace_block(content, RESULTS_FS_START, RESULTS_FS_END,
                             build_table(fewshot, RESULTS_FS_START, RESULTS_FS_END))

    with open(README, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"README.md updated ({len(zeroshot)} zero-shot, {len(fewshot)} few-shot models).")


rows = load_summary()
if rows:
    update_readme(rows)
