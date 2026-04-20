"""
Score model agency-NER predictions against the answer key.

Expects a prediction file named:  mini/narnia_predictions_<model>.csv
with columns: sample_id, sentence_id, predicted_entities
where predicted_entities is a JSON list of {"text": "...", "label": "..."} objects.

Evaluation uses entity-level exact-match precision, recall, and F1.
A predicted entity is correct only if both the character text and agency label
exactly match a gold entity (label comparison is case-insensitive, text is
stripped but case-sensitive to match annotation style).

Usage:
    python narnia/scripts/score_baseline.py --model sonnet
    python narnia/scripts/score_baseline.py --model sonnet --debug

Results are saved to:
    narnia/results/<model>_scores.csv   — per-sample breakdown
    narnia/results/summary.csv          — all models side by side
"""

import os
import csv
import json
import argparse
from collections import defaultdict

HERE     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(HERE)
MINI_DIR = os.path.join(DATA_DIR, "mini")
RES_DIR  = os.path.join(DATA_DIR, "results")

SAMPLE_ID_VARIANTS = {"sample_id", "sample", "sampleid", "sample_num"}
SENT_ID_VARIANTS   = {"sentence_id", "sent_id", "sentid", "id"}


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def load_csv(path):
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [h.strip().lstrip("\ufeff") for h in reader.fieldnames]
        return list(reader)


def normalise_keys(rows):
    if not rows:
        return rows
    remap = {}
    for k in rows[0].keys():
        kl = k.strip().lower()
        if kl in SAMPLE_ID_VARIANTS:
            remap[k] = "sample_id"
        elif kl in SENT_ID_VARIANTS:
            remap[k] = "sentence_id"
    return [{remap.get(k, k): v for k, v in row.items()} for row in rows]


def entity_col(rows):
    skip = SAMPLE_ID_VARIANTS | SENT_ID_VARIANTS
    for col in rows[0].keys():
        if col.strip().lower() not in skip:
            return col
    raise ValueError(f"Could not find entity column in: {list(rows[0].keys())}")


# ---------------------------------------------------------------------------
# Entity parsing
# ---------------------------------------------------------------------------

def parse_entities(raw):
    """
    Parse a JSON entity list from a model response string.
    Returns a set of (text, label) tuples (label uppercased, text stripped).
    Silently returns an empty set on parse errors.
    """
    if not raw or not raw.strip():
        return set()
    raw = raw.strip()
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        try:
            items = json.loads(f"[{raw}]")
        except json.JSONDecodeError:
            return set()
    if not isinstance(items, list):
        return set()
    result = set()
    for item in items:
        if isinstance(item, dict) and "text" in item and "label" in item:
            result.add((str(item["text"]).strip(), str(item["label"]).strip().upper()))
    return result


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def prf(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall    = tp / (tp + fn) if (tp + fn) else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def score_file(pred_path, answer_path, debug=False):
    raw_preds   = load_csv(pred_path)
    raw_answers = load_csv(answer_path)

    if debug:
        print(f"\n  [debug] pred columns  : {list(raw_preds[0].keys()) if raw_preds else 'EMPTY'}")
        print(f"  [debug] answer columns: {list(raw_answers[0].keys())}")
        print(f"  [debug] pred rows     : {len(raw_preds)}")
        print(f"  [debug] answer rows   : {len(raw_answers)}")

    preds   = normalise_keys(raw_preds)
    answers = normalise_keys(raw_answers)

    pred_col = entity_col(preds)
    ans_col  = entity_col(answers)

    pred_lookup = {}
    for r in preds:
        key = (str(r.get("sample_id", "1")).strip(),
               str(r.get("sentence_id", "")).strip())
        pred_lookup[key] = parse_entities(r.get(pred_col, ""))

    by_sample  = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    by_role    = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    for row in answers:
        sid  = str(row.get("sample_id", "1")).strip()
        sent = str(row.get("sentence_id", "")).strip()
        gold = parse_entities(row.get(ans_col, ""))
        pred = pred_lookup.get((sid, sent), set())

        by_sample[sid]["tp"] += len(gold & pred)
        by_sample[sid]["fp"] += len(pred - gold)
        by_sample[sid]["fn"] += len(gold - pred)

        # per-role counts
        gold_labels = {label for _, label in gold}
        pred_labels = {label for _, label in pred}
        all_labels  = gold_labels | pred_labels
        for label in all_labels:
            gold_l = {e for e in gold if e[1] == label}
            pred_l = {e for e in pred if e[1] == label}
            by_role[label]["tp"] += len(gold_l & pred_l)
            by_role[label]["fp"] += len(pred_l - gold_l)
            by_role[label]["fn"] += len(gold_l - pred_l)

        if debug and (gold | pred):
            p, r, f = prf(len(gold & pred), len(pred - gold), len(gold - pred))
            print(f"  [debug] sample={sid} sent={sent}  gold={gold}  pred={pred}  f1={f:.3f}")

    sample_results = []
    for sid in sorted(by_sample):
        tp, fp, fn = by_sample[sid]["tp"], by_sample[sid]["fp"], by_sample[sid]["fn"]
        p, r, f = prf(tp, fp, fn)
        sample_results.append({"sample_id": sid, "precision": p, "recall": r, "f1": f,
                                "tp": tp, "fp": fp, "fn": fn})

    if not sample_results:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "samples": [], "by_role": {}}

    mean_p = sum(s["precision"] for s in sample_results) / len(sample_results)
    mean_r = sum(s["recall"]    for s in sample_results) / len(sample_results)
    mean_f = sum(s["f1"]        for s in sample_results) / len(sample_results)

    role_results = {}
    for label, counts in sorted(by_role.items()):
        p, r, f = prf(counts["tp"], counts["fp"], counts["fn"])
        role_results[label] = {
            "precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4),
            "tp": counts["tp"], "fp": counts["fp"], "fn": counts["fn"],
        }

    return {
        "precision": round(mean_p, 4),
        "recall":    round(mean_r, 4),
        "f1":        round(mean_f, 4),
        "samples":   sample_results,
        "by_role":   role_results,
    }


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def write_csv_file(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def score_model(model, prompt=None, debug=False, per_role=False):
    suffix      = f"_{prompt}" if prompt else ""
    model_key   = f"{model}_{prompt}" if prompt else model
    pred_path   = os.path.join(MINI_DIR, f"narnia_predictions_{model}{suffix}.csv")
    answer_path = os.path.join(MINI_DIR, "narnia_answers.csv")

    if not os.path.exists(pred_path):
        print(f"No predictions file found: {pred_path}")
        return
    if not os.path.exists(answer_path):
        print(f"No answers file found: {answer_path}")
        return

    r = score_file(pred_path, answer_path, debug=debug)

    print(f"\nModel: {model_key}")
    print(f"{'s1_f1':>7}  {'s2_f1':>7}  {'s3_f1':>7}  {'mean_p':>7}  {'mean_r':>7}  {'mean_f1':>8}")
    print("-" * 60)
    cols = [f"{s['f1']:.3f}" for s in r["samples"]] + [""] * (3 - len(r["samples"]))
    print(f"{'  '.join(cols)}  {r['precision']:.3f}    {r['recall']:.3f}    {r['f1']:.3f}")

    if per_role and r["by_role"]:
        print(f"\nPer-role breakdown:")
        print(f"  {'Label':<20}  {'P':>6}  {'R':>6}  {'F1':>6}  {'TP':>4}  {'FP':>4}  {'FN':>4}")
        print(f"  {'-'*20}  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*4}  {'-'*4}  {'-'*4}")
        for label, v in sorted(r["by_role"].items()):
            print(f"  {label:<20}  {v['precision']:>6.3f}  {v['recall']:>6.3f}  {v['f1']:>6.3f}"
                  f"  {v['tp']:>4}  {v['fp']:>4}  {v['fn']:>4}")

    detail_rows = [
        {"model": model_key, "sample": s["sample_id"],
         "precision": round(s["precision"], 4),
         "recall":    round(s["recall"],    4),
         "f1":        round(s["f1"],        4),
         "tp": s["tp"], "fp": s["fp"], "fn": s["fn"]}
        for s in r["samples"]
    ]
    if detail_rows:
        write_csv_file(detail_rows, os.path.join(RES_DIR, f"{model_key}_scores.csv"))

    summary_row  = {"model": model_key, "precision": r["precision"],
                    "recall": r["recall"], "f1": r["f1"]}
    summary_path = os.path.join(RES_DIR, "summary.csv")
    existing = []
    if os.path.exists(summary_path):
        with open(summary_path, encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
        existing = [row for row in existing if row.get("model") != model_key]
    existing.append(summary_row)

    all_keys = ["model", "precision", "recall", "f1"]
    write_csv_file([{k: row.get(k, "") for k in all_keys} for row in existing], summary_path)

    print(f"\nResults saved to  results/{model_key}_scores.csv")
    print(f"Summary updated:  results/summary.csv")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--model",
                       help="score mini predictions for this model (e.g. sonnet, gpt4o)")
    group.add_argument("--predictions",
                       help="path to a single predictions CSV")
    parser.add_argument("--answers",
                       help="answer key CSV (required with --predictions)")
    parser.add_argument("--prompt",
                       help="prompt variant (e.g. fewshot); expects narnia_predictions_<model>_<prompt>.csv")
    parser.add_argument("--debug", action="store_true",
                        help="print per-sentence diagnostics")
    parser.add_argument("--per_role", action="store_true",
                        help="print per-label precision/recall/F1 breakdown")
    args = parser.parse_args()

    if args.model:
        score_model(args.model, prompt=args.prompt, debug=args.debug, per_role=args.per_role)
    else:
        if not args.answers:
            parser.error("--answers is required with --predictions")
        r = score_file(args.predictions, args.answers, debug=args.debug)
        print(f"precision={r['precision']:.3f}  recall={r['recall']:.3f}  f1={r['f1']:.3f}")
        for s in r["samples"]:
            print(f"  sample {s['sample_id']}: p={s['precision']:.3f} r={s['recall']:.3f} f1={s['f1']:.3f}")


if __name__ == "__main__":
    main()
