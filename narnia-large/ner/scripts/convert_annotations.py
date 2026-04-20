"""
Convert the manually annotated narnia CSV to the NER-style JSON entity format.

Input:  narnia/man_annotated_narnia200 - Sheet1.csv
Output: narnia/data/narnia_annotated.csv

Each output row represents one sentence:
    sentence_id, sentence, entities
where entities is a JSON list of {"text": "<character_mention>", "label": "<agency_label>"}.
Sentences with no annotated characters get an empty list [].

Sentence 37 (empty text) is excluded.

Run:
    python narnia/scripts/convert_annotations.py
"""

import os
import csv
import json
from collections import defaultdict

HERE     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(HERE)
SOURCE   = os.path.join(DATA_DIR, "man_annotated_narnia200 - Sheet1.csv")
OUT_DIR  = os.path.join(DATA_DIR, "data")
OUT_FILE = os.path.join(OUT_DIR, "narnia_annotated.csv")


def convert():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Group rows by sentence_id (preserve insertion order = sentence order)
    by_sent = defaultdict(lambda: {"text": "", "entities": []})
    order = []

    with open(SOURCE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row["sentence_id"].strip()
            text = row["sentence_text"].strip()
            mention = row["character_mention"].strip()
            label   = row["label"].strip()

            if sid not in by_sent or not by_sent[sid]["text"]:
                by_sent[sid]["text"] = text
            if sid not in [o for o in order]:
                order.append(sid)

            if mention and label:
                by_sent[sid]["entities"].append({"text": mention, "label": label})

    rows = [["sentence_id", "sentence", "entities"]]
    skipped = 0
    for sid in order:
        text = by_sent[sid]["text"]
        if not text:
            skipped += 1
            continue
        entities = by_sent[sid]["entities"]
        rows.append([sid, text, json.dumps(entities)])

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    n = len(rows) - 1
    print(f"Converted {n} sentences → {OUT_FILE}")
    if skipped:
        print(f"  (skipped {skipped} sentence(s) with empty text)")


if __name__ == "__main__":
    convert()
