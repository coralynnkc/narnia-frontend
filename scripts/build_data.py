#!/usr/bin/env python3
"""
Build narnia_data.json from opus_all_chapters.csv.
Run from repo root: python3 scripts/build_data.py
"""

import csv
import json
import ast
import re
import os
from collections import defaultdict

INPUT_CSV = os.path.join(os.path.dirname(__file__), "../narnia-large/results/opus_all_chapters.csv")
OUTPUT_JSON = os.path.join(os.path.dirname(__file__), "../docs/data/narnia_data.json")

PRONOUN_STOPWORDS = {
    "he", "him", "his", "she", "her", "hers", "they", "them", "their", "theirs",
    "i", "me", "my", "mine", "you", "your", "yours", "we", "us", "our", "ours",
    "it", "its", "who", "that", "this", "these", "those", "what",
}

LABEL_ORDER = [
    "ACTIVE_SPEAKER", "ACTIVE_PERFORMER", "ACTIVE_THOUGHT",
    "ADDRESSED", "MENTIONED_ONLY", "MISCELLANEOUS"
]

ACTIVE_LABELS = {"ACTIVE_SPEAKER", "ACTIVE_PERFORMER", "ACTIVE_THOUGHT"}

# Chapter annotation notes for density chart
CHAPTER_NOTES = {
    8: "Ch.8 — The Beavers",
    12: "Ch.12 — Rescue",
    15: "Ch.15 — Battle",
    17: "Ch.17 — Coronation",
}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def parse_entities(raw):
    if not raw or raw.strip() in ("", "[]"):
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(raw)
        except Exception:
            return []


def generate_blurb(canonical, total, active_ratio, labels, chapters_arr, chapter_first, chapter_last):
    parts = []

    # Active ratio framing
    if active_ratio >= 70:
        parts.append(
            f"{canonical} is one of the most active characters in the narrative — "
            f"with a {active_ratio:.1f}% active agency ratio, they are nearly always speaking, "
            f"acting, or expressing internal thought rather than simply being referenced."
        )
    elif active_ratio >= 50:
        parts.append(
            f"{canonical} has a mixed narrative presence ({active_ratio:.1f}% active agency). "
            f"They appear prominently in dialogue and action scenes but are also frequently "
            f"referenced by other characters in passing."
        )
    else:
        parts.append(
            f"Despite {total} total mentions, {canonical} has a low active agency ratio "
            f"({active_ratio:.1f}%). They function more as a narrative force felt through other "
            f"characters than as a direct actor on the page."
        )

    # Dominant label insight
    dominant = max(labels, key=lambda l: labels.get(l, 0))
    dominant_pct = 100 * labels.get(dominant, 0) / total if total else 0
    mentioned_pct = 100 * labels.get("MENTIONED_ONLY", 0) / total if total else 0

    if dominant == "MENTIONED_ONLY" and mentioned_pct >= 40:
        parts.append(
            f"{mentioned_pct:.0f}% of their mentions are passive (MENTIONED_ONLY) — "
            f"they are talked about far more than they act."
        )
    elif dominant == "ACTIVE_SPEAKER":
        parts.append(
            f"Their most common role is {dominant} ({dominant_pct:.0f}% of mentions), "
            f"reflecting a dialogue-driven presence throughout the story."
        )
    elif dominant == "ACTIVE_PERFORMER":
        parts.append(
            f"Their most common role is {dominant} ({dominant_pct:.0f}% of mentions), "
            f"reflecting a physically active role in the narrative."
        )

    # Chapter range
    active_chapters = [i + 1 for i, c in enumerate(chapters_arr) if c > 0]
    if len(active_chapters) >= 2:
        parts.append(
            f"They appear across {len(active_chapters)} of 17 chapters "
            f"(chapters {active_chapters[0]}–{active_chapters[-1]})."
        )
    elif len(active_chapters) == 1:
        parts.append(f"Their mentions are concentrated in chapter {active_chapters[0]}.")

    return " ".join(parts)


def main():
    # Per-character accumulators
    char_labels = defaultdict(lambda: defaultdict(int))      # canonical -> label -> count
    char_chapters = defaultdict(lambda: defaultdict(int))    # canonical -> chapter -> count
    char_aliases = defaultdict(lambda: defaultdict(int))     # canonical -> surface -> count
    char_sentences = defaultdict(set)                        # canonical -> set of sentence_ids

    # Global accumulators
    label_counts = defaultdict(int)
    chapter_sentences = defaultdict(set)   # chapter -> set of sentence_ids
    chapter_mentions = defaultdict(int)    # chapter -> mention count
    total_mentions = 0

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get("sentence_id", "").strip()
            chapter = row.get("chapter", "").strip()
            try:
                chapter_num = int(float(chapter))
            except (ValueError, TypeError):
                chapter_num = 0

            if sid and chapter_num:
                chapter_sentences[chapter_num].add(sid)

            entities = parse_entities(row.get("entities", ""))
            for ent in entities:
                canonical = ent.get("canonical", "").strip()
                label = ent.get("label", "").strip()
                surface = ent.get("text", "").strip()

                if not canonical or not label:
                    continue

                total_mentions += 1
                label_counts[label] += 1
                chapter_mentions[chapter_num] += 1

                char_labels[canonical][label] += 1
                char_chapters[canonical][chapter_num] += 1
                if sid:
                    char_sentences[canonical].add(sid)

                # Accumulate aliases (clean surface forms)
                surface_lower = surface.lower().strip(",.!?;:\"'()[]")
                if surface_lower and surface_lower not in PRONOUN_STOPWORDS and len(surface_lower) > 1:
                    char_aliases[canonical][surface] += 1

    # Build chapter density
    chapter_density = []
    for ch in range(1, 18):
        n_sentences = len(chapter_sentences.get(ch, set()))
        n_mentions = chapter_mentions.get(ch, 0)
        density = round(n_mentions / n_sentences, 3) if n_sentences > 0 else 0
        chapter_density.append({
            "chapter": ch,
            "sentences": n_sentences,
            "mentions": n_mentions,
            "density": density,
            "note": CHAPTER_NOTES.get(ch, ""),
        })

    total_sentences = sum(len(v) for v in chapter_sentences.values())

    # Build character records
    characters = []
    for canonical, labels in char_labels.items():
        total = sum(labels.values())
        active_count = sum(labels.get(l, 0) for l in ACTIVE_LABELS)
        active_ratio = round(100 * active_count / total, 1) if total else 0

        # 17-element chapters array (index 0 = chapter 1)
        chaps_arr = [char_chapters[canonical].get(ch, 0) for ch in range(1, 18)]

        # Top aliases (sorted by frequency, deduplicated, cleaned)
        alias_items = sorted(char_aliases[canonical].items(), key=lambda x: -x[1])
        aliases = []
        seen_lower = set()
        for surface, _ in alias_items:
            sl = surface.lower().strip()
            if sl not in seen_lower and sl not in PRONOUN_STOPWORDS:
                aliases.append(surface)
                seen_lower.add(sl)
            if len(aliases) >= 10:
                break

        # Full label dict with all 6 labels (0 for missing)
        labels_full = {l: labels.get(l, 0) for l in LABEL_ORDER}

        active_chapters = [i + 1 for i, c in enumerate(chaps_arr) if c > 0]
        chapter_first = active_chapters[0] if active_chapters else 0
        chapter_last = active_chapters[-1] if active_chapters else 0

        blurb = generate_blurb(
            canonical, total, active_ratio, labels_full,
            chaps_arr, chapter_first, chapter_last
        )

        tier = "major" if total >= 5 else "minor"

        characters.append({
            "canonical": canonical,
            "slug": slugify(canonical),
            "total": total,
            "active_ratio": active_ratio,
            "labels": labels_full,
            "chapters": chaps_arr,
            "aliases": aliases,
            "alias_count": len(aliases),
            "blurb": blurb,
            "tier": tier,
            "chapter_first": chapter_first,
            "chapter_last": chapter_last,
            "chapter_count": len(active_chapters),
        })

    # Sort by total mentions descending
    characters.sort(key=lambda c: -c["total"])

    # Build full label_counts with all 6 labels
    label_counts_full = {l: label_counts.get(l, 0) for l in LABEL_ORDER}

    output = {
        "meta": {
            "total_sentences": total_sentences,
            "total_mentions": total_mentions,
            "total_chapters": 17,
            "total_characters": len(characters),
            "major_characters": sum(1 for c in characters if c["tier"] == "major"),
            "label_counts": label_counts_full,
            "chapter_density": chapter_density,
        },
        "characters": characters,
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Done. {len(characters)} characters, {total_mentions} mentions, {total_sentences} sentences.")
    print(f"Output: {OUTPUT_JSON}")

    # Print top 10 for verification
    print("\nTop 10 characters:")
    for c in characters[:10]:
        print(f"  {c['canonical']:30s} total={c['total']:4d}  active={c['active_ratio']:5.1f}%  tier={c['tier']}")


if __name__ == "__main__":
    main()
