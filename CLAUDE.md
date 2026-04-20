# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a text annotation research project — **not a frontend application** despite the directory name. It uses LLMs to annotate character mentions in *The Lion, the Witch and the Wardrobe* (Chronicles of Narnia) with canonical character identities and agency labels.

The sole module is `narnia-large/`, which extends a smaller benchmark to full-chapter analysis.

## Repository Structure

```
narnia-large/
  chapters/         # 17 chapter text files (one sentence per line)
  results/          # Model output CSVs + analysis PNGs
  analysis.ipynb    # Jupyter notebook for aggregating and visualizing results
  README.MD         # Full task spec, label definitions, canonical name mappings, prompts
  scripts/          # (empty or helper scripts)
```

## Task Definition

Given a chapter, a model identifies every character mention sentence-by-sentence and assigns:
1. A **canonical character label** (resolving aliases, e.g. "Faun" → "Mr. Tumnus")
2. An **agency label** from: `ACTIVE_SPEAKER`, `ACTIVE_PERFORMER`, `ACTIVE_THOUGHT`, `ADDRESSED`, `MENTIONED_ONLY`, `MISCELLANEOUS`

## Output Format

Results are saved as CSV with columns: `sentence_id, sentence, entities`

Where `entities` is a JSON list of `{"text": "...", "canonical": "...", "label": "..."}` objects.

File naming: `results/<model>_chapter_<N>.csv` (e.g. `opus_chapter_3.csv`, `sonnet_chapter_1.csv`)

The combined file `results/opus_all_chapters.csv` adds a `chapter` column.

## Running Analysis

Open and run `narnia-large/analysis.ipynb` in Jupyter to generate aggregate stats and the PNG charts in `results/`.

## Adding New Model Results

1. Select a chapter from `chapters/chapter_N.txt`
2. Use the zero-shot or few-shot prompt from `README.MD` with the chapter contents pasted in
3. Save the model response to `results/<model>_chapter_<N>.csv`
4. Re-run `analysis.ipynb` to update aggregates and visualizations

## Key Label Distinctions (common annotation errors)

- Character called by name in dialogue → `ADDRESSED`, not `MENTIONED_ONLY`
- Character's internal state ("Lucy was tired") → `ACTIVE_THOUGHT`, not `ACTIVE_PERFORMER`
- "Son of Adam"/"Daughter of Eve" as direct address → `ADDRESSED`; as species label → `MISCELLANEOUS`
- Sentences with no character mentions → return `[]`
