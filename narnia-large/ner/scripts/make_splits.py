"""
Create 80/20 train/test splits from the annotated narnia data.

Input:  narnia/data/narnia_annotated.csv  (199 sentences)
Output: narnia/data/train.csv             (~159 sentences, 80%)
        narnia/data/test.csv              (~40 sentences, 20%)

Stratified by whether a sentence has any character annotations, so both splits
have a proportional mix of annotated and unannotated sentences.

Run:
    python narnia/scripts/make_splits.py
"""

import os
import csv
import json
import random

HERE     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(HERE)
SOURCE   = os.path.join(DATA_DIR, "data", "narnia_annotated.csv")
TRAIN    = os.path.join(DATA_DIR, "data", "train.csv")
TEST     = os.path.join(DATA_DIR, "data", "test.csv")

SEED       = 42
TEST_RATIO = 0.20


def load_annotated(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stratified_split(rows, test_ratio, rng):
    has_entities    = [r for r in rows if json.loads(r["entities"])]
    no_entities     = [r for r in rows if not json.loads(r["entities"])]

    def split(group):
        n_test = max(1, round(len(group) * test_ratio))
        test_idx = set(rng.sample(range(len(group)), n_test))
        train = [r for i, r in enumerate(group) if i not in test_idx]
        test  = [r for i, r in enumerate(group) if i in test_idx]
        return train, test

    train_e, test_e = split(has_entities)
    train_n, test_n = split(no_entities)

    train = train_e + train_n
    test  = test_e  + test_n
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


rng  = random.Random(SEED)
rows = load_annotated(SOURCE)
train, test = stratified_split(rows, TEST_RATIO, rng)

write_csv(train, TRAIN)
write_csv(test,  TEST)

n_with_train = sum(1 for r in train if json.loads(r["entities"]))
n_with_test  = sum(1 for r in test  if json.loads(r["entities"]))
print(f"Train: {len(train)} sentences  ({n_with_train} with annotations)")
print(f"Test:  {len(test)} sentences  ({n_with_test} with annotations)")
print(f"Files written to {os.path.dirname(TRAIN)}/")
