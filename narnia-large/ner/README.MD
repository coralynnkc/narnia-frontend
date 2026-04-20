# Narnia — Agency-Based Character NER

Source: Chronicles of Narnia — 200 sentences manually annotated with character mentions and their narrative agency role.

## Baseline Results — Entity-level Precision, Recall, F1

<!-- results:start -->
| Model | Precision | Recall | F1 |
| ----- | --------- | ------ | -- |
| sonnet | 0.7154 | 0.7686 | 0.741 |
| opus | 0.7899 | 0.7769 | 0.7833 |
| gemini | 0.561 | 0.5702 | 0.5656 |
| chatgpt | 0.5263 | 0.6612 | 0.5861 |
<!-- results:end -->

_Run `python narnia/scripts/update_readme.py` after scoring to update this table._

## Few-shot Results — Entity-level Precision, Recall, F1

<!-- results-fewshot:start -->
| Model | Precision | Recall | F1 |
| ----- | --------- | ------ | -- |
| gemini_fewshot | 0.7518 | 0.876 | 0.8092 |
| sonnet_fewshot | 0.7698 | 0.8843 | 0.8231 |
| opus_fewshot | 0.7518 | 0.876 | 0.8092 |
| chatgpt_fewshot | 0.731 | 0.876 | 0.797 |
<!-- results-fewshot:end -->

_Run `python narnia/scripts/update_readme.py` after scoring to update this table._

### Per-role F1 (zero-shot)

_Run `python narnia/scripts/score_baseline.py --model <model> --per_role` to reproduce._

| Label | sonnet | opus | chatgpt | gemini |
| ----- | ------ | ---- | ------- | ------ |
| ACTIVE_SPEAKER   | 0.885 | 0.916 | 0.936 | 0.731 |
| ACTIVE_PERFORMER | 0.621 | 0.909 | 0.741 | 0.375 |
| ACTIVE_THOUGHT   | 0.667 | 0.667 | 0.625 | 0.667 |
| ADDRESSED        | 0.529 | 0.571 | 0.851 | 0.600 |
| MENTIONED_ONLY   | 0.702 | 0.704 | 0.600 | 0.348 |
| MISCELLANEOUS    | 0.000 | 0.000 | 0.000 | 0.000 |

### Per-role F1 (few-shot)

_Run `python narnia/scripts/score_baseline.py --model <model> --prompt fewshot --per_role` to reproduce._

| Label | sonnet | opus | chatgpt | gemini | 
| ----- | ------ | ---- | ------- | ------ |
| ACTIVE_SPEAKER   | 0.909 | 0.916 | 0.936 | 0.907 |
| ACTIVE_PERFORMER | 0.640 | 0.783 | 0.741 | 0.643 |
| ACTIVE_THOUGHT   | 0.632 | 0.632 | 0.667 | 0.667 |
| ADDRESSED        | 0.889 | 0.864 | 0.864 | 0.889 |
| MENTIONED_ONLY   | 0.750 | 0.667 | 0.692 | 0.691 |
| MISCELLANEOUS    | 0.800 | 0.667 | 0.250 | 0.800 |

### Qualitative findings (zero-shot)

**ACTIVE_SPEAKER is the easiest label** — all models score above 0.73 F1. The explicit attribution pattern ("said X", "asked X") is unambiguous.

**ADDRESSED is the sharpest discriminator between models.** Sonnet and Opus miss ~60% of ADDRESSED entities (recall ~0.4), while ChatGPT gets 0.85 F1 and Gemini 0.60 F1. The failure mode is treating vocatives as MENTIONED_ONLY — e.g. "Oh, Mr. Tumnus!" where the model assigns no entity rather than tagging Tumnus as ADDRESSED.

**ACTIVE_THOUGHT is consistently weak across all models (0.625–0.667 F1).** The label requires recognizing internal states from narrator language ("Lucy was tired", "she wondered") rather than explicit thought verbs. Models tend to predict ACTIVE_PERFORMER or nothing.

**MISCELLANEOUS gets 0 F1 from every model.** The three gold instances are group/species labels ("Son of Adam", "Daughter of Eve") used neither as direct address nor as named individuals — a subtle distinction the zero-shot prompt does not explain.

**Gemini underperforms on ACTIVE_PERFORMER (0.375 F1) and MENTIONED_ONLY (0.348 F1).** The MENTIONED_ONLY weakness is driven by 34 false positives — Gemini over-predicts this label, applying it to entities that other models correctly tag as ACTIVE_PERFORMER or ACTIVE_SPEAKER.

### Qualitative findings (few-shot)

**ADDRESSED was the biggest beneficiary of few-shot prompting.** Sonnet recall jumped from 0.375 → 0.833 (F1: 0.529 → 0.889); Opus from 0.417 → 0.792 (F1: 0.571 → 0.864). The vocative examples in the prompt directly fixed the most common error mode. ChatGPT was already strong at 0.851 zero-shot and did not change.

**MISCELLANEOUS recovered dramatically for Sonnet and Opus.** Sonnet 0.000 → 0.800, Opus 0.000 → 0.667. The "Son of Adam"/"Daughter of Eve" examples worked exactly as intended. ChatGPT remained at 0.000 (see note below).

**ACTIVE_THOUGHT regressed slightly for Sonnet and Opus** (0.667 → 0.632 for both), despite no change in recall. False positives increased — the richer prompt may be pushing models to over-tag internal states.

**Sonnet gained more from few-shot (+0.082 overall) than Opus (+0.026)**, consistent with Sonnet having more room to improve. The gains are almost entirely from ADDRESSED and MISCELLANEOUS.

**ChatGPT few-shot shows modest but real gains** over zero-shot — overall F1 0.797 vs 0.586. ACTIVE_THOUGHT improved (0.625 → 0.667) and MISCELLANEOUS recovered from 0.000 to 0.250 (F1), though still weak. ADDRESSED and MENTIONED_ONLY also improved slightly. Unlike Sonnet and Opus, ChatGPT did not gain on ACTIVE_PERFORMER.

**Gemini gained the most from few-shot prompting of any model**, improving overall F1 by +0.244 (0.566 → 0.809). Gains span nearly every label: ACTIVE_SPEAKER (0.731 → 0.907), ACTIVE_PERFORMER (0.375 → 0.643), ADDRESSED (0.600 → 0.889), MENTIONED_ONLY (0.348 → 0.691), and MISCELLANEOUS (0.000 → 0.800). The few-shot examples directly fixed Gemini's two main failure modes — over-predicting MENTIONED_ONLY and missing vocatives. Gemini fewshot matches Sonnet fewshot overall (both 0.809 F1).

---

## Task

Given a sentence from _The Lion, the Witch and the Wardrobe_, identify all character mentions and assign each one an agency label describing their narrative role in that sentence.

## Labels

| Label              | Description                                                           |
| ------------------ | --------------------------------------------------------------------- |
| `ACTIVE_SPEAKER`   | Character is mentioned in the context of speaking a dialogue          |
| `ACTIVE_PERFORMER` | Character is written to perform a physical action                     |
| `ACTIVE_THOUGHT`   | Character is written to think or feel something                       |
| `ADDRESSED`        | Character is addressed in dialogue                                    |
| `MENTIONED_ONLY`   | Mentioned by a third-person or narrator                               |
| `MISCELLANEOUS`    | Any other role not covered by the above                               |

---

## Files

| File                                        | Description                                           |
| ------------------------------------------- | ----------------------------------------------------- |
| `man_annotated_narnia200 - Sheet1.csv`      | Raw manual annotations (source of truth)              |
| `data/narnia_annotated.csv`                 | NER-style format: sentence + JSON entity list         |
| `data/train.csv`                            | 80% split (~159 sentences) for few-shot examples      |
| `data/test.csv`                             | 20% split (~40 sentences) for evaluation              |
| `mini/narnia_input.csv`                     | Model-facing eval input (no labels)                   |
| `mini/narnia_answers.csv`                   | Gold answer key (JSON entity lists)                   |
| `mini/narnia_predictions_<model>.csv`       | Model predictions (save here after running a model)   |

### Data Format

`narnia_annotated.csv` and the split files share the same schema:

```
sentence_id, sentence, entities
```

where `entities` is a JSON list of `{"text": "...", "label": "..."}` objects:

```
38,Badgers ! said Lucy .,"[{""text"": ""Lucy"", ""label"": ""ACTIVE_SPEAKER""}]"
2,This story is about something that happened to them ...,[]
```

Sentences with no annotated characters have `entities = []`.

---

## Baselining

### Workflow

1. _(One-time, already done)_ Convert raw annotations and create splits:

   ```bash
   python narnia/scripts/convert_annotations.py
   python narnia/scripts/make_splits.py
   python narnia/scripts/make_mini.py
   ```

   `make_mini.py` creates `mini/narnia_input.csv` and `mini/narnia_answers.csv` — all 199 sentences in shuffled order.

2. Send the prompt below with `mini/narnia_input.csv` pasted in. Save the response as:

   ```
   mini/narnia_predictions_<model>.csv
   ```

3. Score:

   ```bash
   python narnia/scripts/score_baseline.py --model <model>
   ```

   Repeat steps 2–3 for each model.

4. For few-shot runs, use the few-shot prompt (see below). Save the response as:

   ```
   mini/narnia_predictions_<model>_fewshot.csv
   ```

5. Score few-shot predictions with the `--prompt fewshot` flag:

   ```bash
   python narnia/scripts/score_baseline.py --model <model> --prompt fewshot
   ```

6. Update this README:

   ```bash
   python narnia/scripts/update_readme.py
   ```

Scores are saved to:

- `results/<model>_scores.csv` — precision, recall, F1, TP/FP/FN per sample
- `results/<model>_fewshot_scores.csv` — same for few-shot runs
- `results/summary.csv` — all models side by side

---

## Prompts

### Zero-shot prompt (baseline)

Paste the contents of `mini/narnia_input.csv` directly after this message:

```
For each row, identify all character mentions in the sentence and assign each one an agency label.
Return ONLY a CSV saved as narnia_predictions_[model].csv with columns: sample_id,sentence_id,predicted_entities
where predicted_entities is a JSON list of {"text": "...", "label": "..."} objects.
No explanation. Do not skip rows.

Valid labels: ACTIVE_SPEAKER, ACTIVE_PERFORMER, ACTIVE_THOUGHT, ADDRESSED, MENTIONED_ONLY, MISCELLANEOUS

Label definitions:
- ACTIVE_SPEAKER: character is mentioned in the context of speaking a dialogue
- ACTIVE_PERFORMER: character is written to perform a physical action
- ACTIVE_THOUGHT: character is written to think or feel something
- ADDRESSED: character is addressed in dialogue
- MENTIONED_ONLY: mentioned by a third-person or narrator
- MISCELLANEOUS: any other role

If a sentence has no character mentions, return an empty list: []

Example input row:  1,1,Badgers ! said Lucy .
Example output row: 1,1,"[{""text"": ""Lucy"", ""label"": ""ACTIVE_SPEAKER""}]"

Example input row:  1,2,This story is about something that happened to them when they were sent away .
Example output row: 1,2,[]

Data:
[paste contents of mini/narnia_input.csv here]
```

---

### Few-shot prompt

Paste the contents of `mini/narnia_input.csv` after the examples block below.
Save the response as `mini/narnia_predictions_<model>_fewshot.csv`.

```
You are annotating sentences from The Chronicles of Narnia for character agency.

For each row, identify all character or group mentions and assign each one an agency label.
Return ONLY a CSV named narnia_predictions_[model]_fewshot.csv with columns: sample_id,sentence_id,predicted_entities
where predicted_entities is a JSON list of {"text": "...", "label": "..."} objects.
No explanation. Do not skip rows.

Valid labels:
- ACTIVE_SPEAKER   — character is speaking (look for "said X", "asked X", dialogue attribution)
- ACTIVE_PERFORMER — character performs a physical action (look for action verbs with character as subject)
- ACTIVE_THOUGHT   — character thinks, feels, wonders, or has an internal state
- ADDRESSED        — character is spoken to or called by name in dialogue (vocatives, direct address)
- MENTIONED_ONLY   — character is named by the narrator or in third-person reference, with no agency
- MISCELLANEOUS    — group or species labels used as names (e.g. "Son of Adam", "Daughter of Eve"), or roles that don't fit above

Key distinctions:
- A character called by name in speech ("Oh, Mr. Tumnus!") is ADDRESSED, not MENTIONED_ONLY.
- A character's feeling or internal state ("Lucy was tired", "Lucy thought") is ACTIVE_THOUGHT, not ACTIVE_PERFORMER.
- "Son of Adam" / "Daughter of Eve" / "Faun" used as a form of address → ADDRESSED; used as a species label → MISCELLANEOUS.
- If a sentence has no character mentions, return [].

--- EXAMPLES ---

Input:  1,1,It 's only just back there -- at least -- I 'm not sure .
Output: 1,1,[]

Input:  1,2,"This is the land of Narnia , said the Faun , "" where we are now ; all that lies between the lamp - post and the great castle of Cair Paravel on the eastern sea ."""
Output: 1,2,"[{""text"": ""Faun"", ""label"": ""ACTIVE_SPEAKER""}]"

Input:  1,3,But the Faun continued sobbing as if his heart would break .
Output: 1,3,"[{""text"": ""Faun"", ""label"": ""ACTIVE_PERFORMER""}]"

Input:  1,4,He was a Faun .
Output: 1,4,"[{""text"": ""Faun"", ""label"": ""MENTIONED_ONLY""}]"

Input:  1,5,And when Lucy was tired of eating the Faun began to talk .
Output: 1,5,"[{""text"": ""Lucy"", ""label"": ""ACTIVE_THOUGHT""}]"

Input:  1,6,You are the nicest Faun I 've ever met .
Output: 1,6,"[{""text"": ""Faun"", ""label"": ""ADDRESSED""}]"

Input:  1,7,But I 've never seen a Son of Adam or a Daughter of Eve before .
Output: 1,7,"[{""text"": ""Son of Adam"", ""label"": ""MISCELLANEOUS""}, {""text"": ""Daughter of Eve"", ""label"": ""MISCELLANEOUS""}]"

Input:  1,8,"And may I ask , O Lucy , Daughter of Eve , said Mr. Tumnus , "" how you have come into Narnia ? """
Output: 1,8,"[{""text"": ""Lucy"", ""label"": ""ADDRESSED""}, {""text"": ""Daughter of Eve"", ""label"": ""ADDRESSED""}, {""text"": ""Mr. Tumnus"", ""label"": ""ACTIVE_SPEAKER""}]"

--- DATA ---
[paste contents of mini/narnia_input.csv here]
```
