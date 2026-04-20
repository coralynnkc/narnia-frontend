# Coref — Character Coreference NER (Narnia)

multi-label entity categorization through coreference objects in narnia

Source: Chronicles of Narnia — same 199 sentences used in agency-based NER (`narnia/`), re-annotated for character identity resolution.

## Task

Given a sentence, identify all character mentions and assign each one their canonical character name. The model must resolve both named references ("the Faun", "the Professor") and nicknames to the correct canonical label — this is NER where the label set is the set of characters, not entity types.

Combined with the agency labels from `narnia/`, each `(span, character, agency_role)` triple enables corpus-level insights like "how often is Lucy Pevensie an ACTIVE_SPEAKER?"

## Canonical Characters

| Canonical name         | Notes           |
| ---------------------- | --------------- |
| Peter Pevensie         |                 |
| Susan Pevensie         |                 |
| Edmund Pevensie        |                 |
| Lucy Pevensie          |                 |
| Professor Digory Kirke |                 |
| Mrs. Macready          |                 |
| Mr. Tumnus             |                 |
| Jadis                  | the White Witch |
| Bacchus                |                 |
| Silenus                |                 |
| Ivy                    | servant         |
| Margaret               | servant         |
| Betty                  | servant         |

## Baseline Results — Entity-level Precision, Recall, F1

<!-- results:start -->

| Model   | Precision | Recall | F1     |
| ------- | --------- | ------ | ------ |
| opus    | 0.8699    | 0.8992 | 0.8843 |
| sonnet  | 0.7355    | 0.7479 | 0.7417 |
| chatgpt | 0.2801    | 0.7815 | 0.4124 |

<!-- results:end -->

_Run `python coref/scripts/update_readme.py` after scoring to update this table._

## Few-shot Results — Entity-level Precision, Recall, F1

<!-- results-fewshot:start -->

| Model           | Precision | Recall | F1     |
| --------------- | --------- | ------ | ------ |
| sonnet_fewshot  | 0.7481    | 0.8487 | 0.7953 |
| opus_fewshot    | 0.8       | 0.8403 | 0.8197 |
| chatgpt_fewshot | 0.4056    | 0.8487 | 0.5489 |

<!-- results-fewshot:end -->

_Run `python coref/scripts/update_readme.py` after scoring to update this table._

### Per-character F1 (zero-shot)

_Run `python coref/scripts/score_baseline.py --model <model> --per_character` to reproduce._

| Character              | opus  | sonnet | chatgpt |
| ---------------------- | ----- | ------ | ------- |
| Peter Pevensie         | 1.000 | 1.000  | 0.522   |
| Susan Pevensie         | 0.909 | 0.909  | 0.455   |
| Edmund Pevensie        | 0.889 | 0.889  | 0.516   |
| Lucy Pevensie          | 0.901 | 0.911  | 0.462   |
| Professor Digory Kirke | 1.000 | 0.333  | 0.143   |
| Mrs. Macready          | 1.000 | 1.000  | 0.500   |
| Mr. Tumnus             | 0.861 | 0.550  | 0.342   |
| Jadis                  | 0.800 | 0.000  | 0.000   |
| Bacchus                | 1.000 | 1.000  | 1.000   |
| Silenus                | 0.667 | 0.667  | 0.667   |
| Ivy                    | 1.000 | 1.000  | 1.000   |
| Margaret               | 1.000 | 1.000  | 1.000   |
| Betty                  | 1.000 | 1.000  | 1.000   |

### Per-character F1 (few-shot)

_Run `python coref/scripts/score_baseline.py --model <model> --prompt fewshot --per_character` to reproduce._

| Character              | opus  | sonnet | chatgpt |
| ---------------------- | ----- | ------ | ------- |
| Peter Pevensie         | 1.000 | 1.000  | 1.000   |
| Susan Pevensie         | 0.909 | 0.909  | 0.909   |
| Edmund Pevensie        | 0.889 | 0.889  | 0.727   |
| Lucy Pevensie          | 0.737 | 0.673  | 0.521   |
| Professor Digory Kirke | 1.000 | 1.000  | 0.308   |
| Mrs. Macready          | 1.000 | 1.000  | 1.000   |
| Mr. Tumnus             | 0.857 | 0.872  | 0.529   |
| Jadis                  | 0.800 | 0.800  | 0.000   |
| Bacchus                | 1.000 | 1.000  | 1.000   |
| Silenus                | 0.667 | 0.667  | 0.667   |
| Ivy                    | 1.000 | 1.000  | 1.000   |
| Margaret               | 1.000 | 1.000  | 1.000   |
| Betty                  | 1.000 | 1.000  | 1.000   |

### Qualitative findings (zero-shot)

**Opus is the strongest model by a large margin.** F1 0.884 vs. sonnet 0.742 — the gap is driven almost entirely by epithet resolution: opus correctly maps "the Faun", "the Witch", "the Professor" to their canonical names while sonnet and chatgpt frequently fail.

**Mr. Tumnus is the hardest character to resolve zero-shot.** Sonnet scores only F1 0.550 (15 FP, 21 FN) — the failure mode is inconsistency: "Mr. Tumnus" gets resolved correctly but "the Faun" often does not, or gets mapped to an incorrect character. Opus handles both surface forms reliably (F1 0.861).

**Jadis is a complete zero for sonnet and chatgpt zero-shot.** Both score F1 0.000 — sonnet predicts no Jadis mentions at all (4 FN, 0 TP); chatgpt over-predicts wildly (9 FP, 4 FN) but never correctly. Opus gets F1 0.800. The likely failure mode is that "the White Witch" and "she" are not linked to the canonical name "Jadis" without a prompt cue.

**Professor Digory Kirke collapses for sonnet zero-shot (F1 0.333).** Only 1 of 3 gold mentions is correctly resolved; the other two are predicted as a different character or missed entirely. This is surprising given "the Professor" is used consistently — the issue may be that sonnet defaults to a generic NER label rather than the canonical name.

**ChatGPT's precision is catastrophically low across all characters (0.28 overall).** High recall but massive over-prediction: Lucy Pevensie alone has 91 FP vs. 40 TP. This is the same qualitative failure mode as its CoNLL-2003 NER result — the model tags far too many spans and assigns character labels to narrators, objects, and non-entities.

### Qualitative findings (few-shot)

**Few-shot examples fix the epithet problem for sonnet but not chatgpt.** Sonnet jumps from F1 0.000 → 0.800 on Jadis and 0.333 → 1.000 on Professor Digory Kirke — both directly addressed by prompt examples. Chatgpt remains at 0.000 on Jadis despite the same examples, confirming the over-prediction failure is structural, not a missing cue.

**Opus regresses on Lucy Pevensie few-shot (0.901 → 0.737).** Precision drops (18 FP vs. 8 FP zero-shot) while recall also falls. The richer prompt appears to make opus over-apply the "Lucy" label — possibly confusing pronoun resolution with explicit mention tagging.

**Sonnet's Mr. Tumnus resolution improves dramatically (+0.322 F1).** The "the Faun" → Mr. Tumnus example in the few-shot prompt directly fixes the dominant error. FP drop from 15 → 1 (almost no hallucinated Tumnus mentions), FN from 21 → 9.

**Few-shot does not fix ChatGPT's precision problem.** Precision rises from 0.28 → 0.41 but remains far below opus (0.80) and sonnet (0.75). FP counts stay high: Lucy 63 FP, Mr. Tumnus 60 FP. The gain in overall F1 (0.412 → 0.549) comes from recall improvement, not fixing over-prediction.

**Silenus is consistently weak across all models and conditions (F1 0.667).** Only 1 gold mention in the dataset — every model gets it right but also produces 1 FP, giving consistent P=0.5, R=1.0. Too few instances to draw conclusions.

---

## Data Format

`data/narnia_coref_annotated.csv` shares the same schema as `narnia/data/narnia_annotated.csv`:

```
sentence_id, sentence, entities
```

where `entities` is a JSON list of `{"text": "...", "character": "..."}` objects:

```
1,"Once there were four children whose names were Peter , Susan , Edmund and Lucy .","[{""text"": ""Peter"", ""character"": ""Peter Pevensie""}, {""text"": ""Susan"", ""character"": ""Susan Pevensie""}, ...]"
2,This story is about something that happened to them ...,[]
```

Sentences with no character mentions have `entities = []`.

---

## Files

| File                                        | Description                                         |
| ------------------------------------------- | --------------------------------------------------- |
| `data/narnia_coref_annotated.csv`           | Character NER format: sentence + JSON entity list   |
| `mini/narnia_coref_input.csv`               | Model-facing eval input (no labels)                 |
| `mini/narnia_coref_answers.csv`             | Gold answer key (JSON entity lists)                 |
| `mini/narnia_coref_predictions_<model>.csv` | Model predictions (save here after running a model) |

---

## Workflow

1. _(One-time)_ Convert raw annotations and generate mini eval files:

   ```bash
   python coref/scripts/convert_annotations.py
   python coref/scripts/make_mini.py
   ```

2. Send the prompt below with `mini/narnia_coref_input.csv` pasted in. Save the response as:

   ```
   mini/narnia_coref_predictions_<model>.csv
   ```

3. Score:

   ```bash
   python coref/scripts/score_baseline.py --model <model>
   python coref/scripts/score_baseline.py --model <model> --per_character
   ```

4. For few-shot runs, use the few-shot prompt. Save the response as:

   ```
   mini/narnia_coref_predictions_<model>_fewshot.csv
   ```

5. Score few-shot:

   ```bash
   python coref/scripts/score_baseline.py --model <model> --prompt fewshot
   ```

6. Update this README:

   ```bash
   python coref/scripts/update_readme.py
   ```

Scores are saved to:

- `results/<model>_scores.csv` — precision, recall, F1, TP/FP/FN per sample
- `results/<model>_fewshot_scores.csv` — same for few-shot runs
- `results/summary.csv` — all models side by side

---

## Prompts

### Zero-shot prompt

Paste the contents of `mini/narnia_coref_input.csv` directly after this message.
Save the response as `mini/narnia_coref_predictions_[model].csv`.

```
For each row, identify all character mentions in the sentence and assign each one their canonical character name.
Return ONLY a CSV saved as narnia_coref_predictions_[model].csv with columns: sample_id,sentence_id,predicted_entities
where predicted_entities is a JSON list of {"text": "...", "character": "..."} objects.
No explanation. Do not skip rows.

Valid canonical character names:
- Peter Pevensie
- Susan Pevensie
- Edmund Pevensie
- Lucy Pevensie
- Professor Digory Kirke
- Mrs. Macready
- Mr. Tumnus
- Jadis
- Bacchus
- Silenus
- Ivy
- Margaret
- Betty

Assign every mention — including epithets and titles — to the correct canonical name.
If a sentence has no character mentions, return an empty list: []

Example input:  1,1,Once there were four children whose names were Peter , Susan , Edmund and Lucy .
Example output: 1,1,"[{""text"": ""Peter"", ""character"": ""Peter Pevensie""}, {""text"": ""Susan"", ""character"": ""Susan Pevensie""}, {""text"": ""Edmund"", ""character"": ""Edmund Pevensie""}, {""text"": ""Lucy"", ""character"": ""Lucy Pevensie""}]"

Example input:  1,2,This story is about something that happened to them .
Example output: 1,2,[]

Data:
[paste contents of mini/narnia_coref_input.csv here]
```

---

### Few-shot prompt

Paste the contents of `mini/narnia_coref_input.csv` after the examples block below.
Save the response as `mini/narnia_coref_predictions_[model]_fewshot.csv`.

```
You are annotating sentences from The Chronicles of Narnia for character coreference.

For each row, identify all character mentions in the sentence and assign each one
their canonical character name. Return ONLY a CSV saved as narnia_coref_predictions_[model]_fewshot.csv
with columns: sample_id,sentence_id,predicted_entities
where predicted_entities is a JSON list of {"text": "...", "character": "..."} objects.
No explanation. Do not skip rows.

Valid canonical character names:
- Peter Pevensie
- Susan Pevensie
- Edmund Pevensie
- Lucy Pevensie
- Professor Digory Kirke
- Mrs. Macready
- Mr. Tumnus
- Jadis
- Bacchus
- Silenus
- Ivy
- Margaret
- Betty

Key rules:
- The text field should be the span as it appears in the sentence.
- Resolve all epithets and titles to the correct canonical name (e.g. "the Faun" → Mr. Tumnus, "the Professor" → Professor Digory Kirke, "the White Witch" → Jadis).
- If a sentence has no character mentions, return [].

--- EXAMPLES ---

Input:  1,1,Once there were four children whose names were Peter , Susan , Edmund and Lucy .
Output: 1,1,"[{""text"": ""Peter"", ""character"": ""Peter Pevensie""}, {""text"": ""Susan"", ""character"": ""Susan Pevensie""}, {""text"": ""Edmund"", ""character"": ""Edmund Pevensie""}, {""text"": ""Lucy"", ""character"": ""Lucy Pevensie""}]"

Input:  1,2,This story is about something that happened to them when they were sent away .
Output: 1,2,[]

Input:  1,3,"This is the land of Narnia , said the Faun , where we are now ."
Output: 1,3,"[{""text"": ""Faun"", ""character"": ""Mr. Tumnus""}]"

Input:  1,4,"They were sent to the house of an old Professor who lived in the heart of the country ."
Output: 1,4,"[{""text"": ""Professor"", ""character"": ""Professor Digory Kirke""}]"

Input:  1,5,He had no wife and he lived in a very large house with a housekeeper called Mrs. Macready and three servants .
Output: 1,5,"[{""text"": ""Mrs. Macready"", ""character"": ""Mrs. Macready""}]"

Input:  1,6,"And may I ask , O Lucy , said Mr. Tumnus , how you have come into Narnia ?"
Output: 1,6,"[{""text"": ""Lucy"", ""character"": ""Lucy Pevensie""}, {""text"": ""Mr. Tumnus"", ""character"": ""Mr. Tumnus""}]"

Input:  1,7,"It was she who had enchanted the whole country so that it was always winter ."
Output: 1,7,"[{""text"": ""she"", ""character"": ""Jadis""}]"

--- DATA ---
[paste contents of mini/narnia_coref_input.csv here]
```
