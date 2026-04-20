"""
Generate mini evaluation sets for manual LLM baselining.

Task: given a sentence, identify character mentions and their agency role.

Reads narnia/data/narnia_annotated.csv (all 199 sentences) and writes a single
sample in shuffled order (not contiguous — preserving sequential context would
let models infer labels from narrative flow).

Output:
    mini/narnia_input.csv    — sentences for the model (no labels)
    mini/narnia_answers.csv  — gold entity lists as JSON

Run:
    python narnia/scripts/make_mini.py
"""

import os
import csv
import random

HERE     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(HERE)
SOURCE   = os.path.join(DATA_DIR, "data", "narnia_annotated.csv")
OUT_DIR  = os.path.join(DATA_DIR, "mini")

SEED = 42


def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


print(f"Reading {SOURCE} ...")
sentences = load_csv(SOURCE)
print(f"  {len(sentences)} sentences loaded")

rng = random.Random(SEED)
rng.shuffle(sentences)

input_rows  = [["sample_id", "sentence_id", "sentence"]]
answer_rows = [["sample_id", "sentence_id", "entities"]]

for sent_num, row in enumerate(sentences, start=1):
    input_rows.append([1, sent_num, row["sentence"]])
    answer_rows.append([1, sent_num, row["entities"]])

write_csv(input_rows,  os.path.join(OUT_DIR, "narnia_input.csv"))
write_csv(answer_rows, os.path.join(OUT_DIR, "narnia_answers.csv"))

n = len(input_rows) - 1
print(f"  {n} rows written  (1 sample, all sentences)")
print(f"\nDone. Files in {OUT_DIR}/")
print("Upload narnia_input.csv to a model, save output as narnia_predictions_<model>.csv")
