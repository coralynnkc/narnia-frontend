"""
Convert the narnia manual annotations to character-label NER format for coreference evaluation.

Input:  narnia/man_annotated_narnia200 - Sheet1.csv
Output: coref/data/narnia_coref_annotated.csv

Each output row represents one sentence:
    sentence_id, sentence, entities
where entities is a JSON list of {"text": "<character_mention>", "character": "<canonical_name>"} objects.
Sentences with no annotated characters get entities = [].

Run:
    python coref/scripts/convert_annotations.py
"""

import os
import csv
import json
from collections import OrderedDict

HERE       = os.path.dirname(os.path.abspath(__file__))
COREF_DIR  = os.path.dirname(HERE)
REPO_ROOT  = os.path.dirname(COREF_DIR)
SOURCE     = os.path.join(REPO_ROOT, "narnia", "man_annotated_narnia200 - Sheet1.csv")
OUT_DIR    = os.path.join(COREF_DIR, "data")
OUT_FILE   = os.path.join(OUT_DIR, "narnia_coref_annotated.csv")


def convert():
    os.makedirs(OUT_DIR, exist_ok=True)

    # sentence_id -> {"text": str, "entities": [{"text": mention, "character": canonical}, ...]}
    by_sent = OrderedDict()

    with open(SOURCE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid       = row["sentence_id"].strip()
            text      = row["sentence_text"].strip()
            mention   = row["character_mention"].strip()
            canonical = row["canonical_character"].strip()

            if sid not in by_sent:
                by_sent[sid] = {"text": text, "entities": []}
            elif not by_sent[sid]["text"] and text:
                by_sent[sid]["text"] = text

            if mention and canonical:
                by_sent[sid]["entities"].append({"text": mention, "character": canonical})

    rows = [["sentence_id", "sentence", "entities"]]
    skipped = 0
    for sid, data in by_sent.items():
        if not data["text"]:
            skipped += 1
            continue
        rows.append([sid, data["text"], json.dumps(data["entities"])])

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    n = len(rows) - 1
    print(f"Converted {n} sentences → {OUT_FILE}")
    if skipped:
        print(f"  (skipped {skipped} sentence(s) with empty text)")


if __name__ == "__main__":
    convert()
