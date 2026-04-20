# Narnia Large-Scale — Chapter-Level Agency NER

Source: Chronicles of Narnia (*The Lion, the Witch and the Wardrobe*) — 17 chapters, full text.

This module extends the `narnia/` mini-eval to whole-chapter analysis. Rather than a 200-sentence annotated benchmark, input is a full chapter document and the model returns one entity record per character mention, including surface text, canonical character identity, and agency label.

## Task

Given a chapter from *The Lion, the Witch and the Wardrobe*, identify every character mention sentence by sentence and assign each one:

1. A **canonical character label** — the character's consistent identity across name variants (e.g. "Faun" → "Mr. Tumnus", "Ed" → "Edmund Pevensie")
2. An **agency label** — the character's narrative role in that sentence

## Labels

| Label              | Description                                                           |
| ------------------ | --------------------------------------------------------------------- |
| `ACTIVE_SPEAKER`   | Character is mentioned in the context of speaking a dialogue          |
| `ACTIVE_PERFORMER` | Character is written to perform a physical action                     |
| `ACTIVE_THOUGHT`   | Character is written to think or feel something                       |
| `ADDRESSED`        | Character is addressed in dialogue                                    |
| `MENTIONED_ONLY`   | Mentioned by a third-person or narrator                               |
| `MISCELLANEOUS`    | Any other role not covered by the above                               |

## Canonical Character Labels

These are sourced from the `coref/` module annotations.

| Surface forms                                           | Canonical label                    |
| ------------------------------------------------------- | ---------------------------------- |
| Lucy, Lu                                                | Lucy Pevensie                      |
| Peter                                                   | Peter Pevensie                     |
| Susan, Su                                               | Susan Pevensie                     |
| Edmund, Ed                                              | Edmund Pevensie                    |
| Mother                                                  | Mrs. Pevensie                      |
| Mr. Tumnus, Tumnus, Faun, the Faun                      | Mr. Tumnus                         |
| the White Witch, the Queen, Jadis, Her Imperial Majesty | Jadis                              |
| Aslan, the Lion                                         | Aslan                              |
| Professor, Professor Kirke                              | Professor Digory Kirke             |
| Mrs. Macready                                           | Mrs. Macready                      |
| Father Christmas                                        | Father Christmas                   |
| Daughter of Eve (addressing Lucy specifically)          | Lucy Pevensie                      |
| Son of Adam (addressing Peter or Edmund)                | Peter Pevensie / Edmund Pevensie   |
| Daughter of Eve / Son of Adam (generic species label)   | (use surface form)                 |

If a character cannot be resolved to a known canonical label, use the most complete name form available in the text.

## Output Format

Each entity is a JSON object with three fields:

```json
{"text": "<surface mention>", "canonical": "<canonical character label>", "label": "<agency label>"}
```

Example:

```
sentence_id,sentence,entities
6,"But the Faun continued sobbing as if his heart would break .","[{""text"": ""Faun"", ""canonical"": ""Mr. Tumnus"", ""label"": ""ACTIVE_PERFORMER""}]"
12,"""Do n't go on talking like that . "" said Ed ","[{""text"": ""Ed"", ""canonical"": ""Edmund Pevensie"", ""label"": ""ACTIVE_SPEAKER""}]"
```

---

## Files

| File                                    | Description                                            |
| --------------------------------------- | ------------------------------------------------------ |
| `chapters/chapter_N.txt`                | Full chapter text, one sentence per line               |
| `results/<model>_chapter_N.csv`         | Model output for chapter N (sentence_id, sentence, entities) |
| `results/summary.csv`                   | Aggregated stats across chapters and models            |

---

## Workflow

1. Select a chapter file from `chapters/`.
2. Send the prompt below with the chapter contents pasted in.
3. Save the model's response to:

   ```
   results/<model>_chapter_<N>.csv
   ```

4. (Scoring scripts TBD — this module is under active development.)

---

## Prompt

### Zero-shot (chapter-level)

Paste the contents of a `chapters/chapter_N.txt` file after the prompt below.

```
Save output as: results/<model>_chapter_<N>.csv

You are annotating a chapter from The Lion, the Witch and the Wardrobe for character agency.

For each sentence, identify all character mentions and assign each one an agency label.
Return ONLY a CSV with columns: sentence_id,sentence,entities
where entities is a JSON list of {"text": "...", "canonical": "...", "label": "..."} objects.
- "text" is the surface form of the mention as it appears in the sentence.
- "canonical" is the character's consistent canonical name (resolve aliases: "Faun" → "Mr. Tumnus", "Ed" → "Edmund Pevensie", etc.).
- "label" is the agency label for that sentence.
No explanation. Do not skip sentences. Number sentences starting from 1.

Valid labels: ACTIVE_SPEAKER, ACTIVE_PERFORMER, ACTIVE_THOUGHT, ADDRESSED, MENTIONED_ONLY, MISCELLANEOUS

Label definitions:
- ACTIVE_SPEAKER: character is mentioned in the context of speaking a dialogue
- ACTIVE_PERFORMER: character is written to perform a physical action
- ACTIVE_THOUGHT: character is written to think or feel something
- ADDRESSED: character is addressed in dialogue (vocatives, direct address)
- MENTIONED_ONLY: mentioned by a third-person or narrator, no agency
- MISCELLANEOUS: any other role (group/species labels used as names, etc.)

Key distinctions:
- A character called by name in speech ("Oh, Mr. Tumnus!") is ADDRESSED, not MENTIONED_ONLY.
- A character's feeling or internal state ("Lucy was tired") is ACTIVE_THOUGHT, not ACTIVE_PERFORMER.
- "Son of Adam" / "Daughter of Eve" used as direct address → ADDRESSED; used as species label → MISCELLANEOUS.
- If a sentence has no character mentions, return [].

Canonical name mappings (resolve these automatically):
- Faun / the Faun / Tumnus / Mr. Tumnus → Mr. Tumnus
- Ed → Edmund Pevensie
- Lu / Lucy → Lucy Pevensie
- Peter → Peter Pevensie
- Susan / Su → Susan Pevensie
- Mother → Mrs. Pevensie
- the White Witch / the Queen / Jadis / Her Imperial Majesty → Jadis
- the Lion / Aslan → Aslan
- the Professor / Professor Kirke → Professor Digory Kirke
- Daughter of Eve (when addressing Lucy) → Lucy Pevensie
- Son of Adam (when addressing Peter or Edmund) → use context to resolve

Example input sentence (sentence 3):
  But the Faun continued sobbing as if his heart would break .
Example output row:
  3,"But the Faun continued sobbing as if his heart would break .","[{""text"": ""Faun"", ""canonical"": ""Mr. Tumnus"", ""label"": ""ACTIVE_PERFORMER""}]"

Example input sentence (sentence 8):
  And may I ask , O Lucy , Daughter of Eve , said Mr. Tumnus , how you have come into Narnia ?
Example output row:
  8,"And may I ask , O Lucy , Daughter of Eve , said Mr. Tumnus , how you have come into Narnia ?","[{""text"": ""Lucy"", ""canonical"": ""Lucy Pevensie"", ""label"": ""ADDRESSED""}, {""text"": ""Daughter of Eve"", ""canonical"": ""Lucy Pevensie"", ""label"": ""ADDRESSED""}, {""text"": ""Mr. Tumnus"", ""canonical"": ""Mr. Tumnus"", ""label"": ""ACTIVE_SPEAKER""}]"

Data:
[paste contents of chapters/chapter_N.txt here]
```

---

### Few-shot (chapter-level)

```
Save output as: results/<model>_chapter_<N>.csv

You are annotating a chapter from The Lion, the Witch and the Wardrobe for character agency.

For each sentence, identify all character mentions and assign each one an agency label.
Return ONLY a CSV with columns: sentence_id,sentence,entities
where entities is a JSON list of {"text": "...", "canonical": "...", "label": "..."} objects.
- "text" is the surface form of the mention as it appears in the sentence.
- "canonical" is the character's consistent canonical name (resolve aliases).
- "label" is the agency label for that sentence.
No explanation. Do not skip sentences. Number sentences starting from 1.

Valid labels:
- ACTIVE_SPEAKER   — character is speaking (look for "said X", "asked X", dialogue attribution)
- ACTIVE_PERFORMER — character performs a physical action (action verbs with character as subject)
- ACTIVE_THOUGHT   — character thinks, feels, wonders, or has an internal state
- ADDRESSED        — character is spoken to or called by name in dialogue (vocatives, direct address)
- MENTIONED_ONLY   — character is named by the narrator or in third-person reference, no agency
- MISCELLANEOUS    — group/species labels used as names, or roles that don't fit above

Key distinctions:
- A character called by name in speech ("Oh, Mr. Tumnus!") is ADDRESSED, not MENTIONED_ONLY.
- A character's feeling or internal state ("Lucy was tired") is ACTIVE_THOUGHT, not ACTIVE_PERFORMER.
- "Son of Adam" / "Daughter of Eve" used as direct address → ADDRESSED; used as species label → MISCELLANEOUS.
- If a sentence has no character mentions, return [].

Canonical name mappings (resolve these automatically):
- Faun / the Faun / Tumnus / Mr. Tumnus → Mr. Tumnus
- Ed → Edmund Pevensie
- Lu / Lucy → Lucy Pevensie
- Peter → Peter Pevensie
- Susan / Su → Susan Pevensie
- Mother → Mrs. Pevensie
- the White Witch / the Queen / Jadis / Her Imperial Majesty → Jadis
- the Lion / Aslan → Aslan
- the Professor / Professor Kirke → Professor Digory Kirke
- Daughter of Eve (when addressing Lucy) → Lucy Pevensie
- Son of Adam (when addressing Peter or Edmund) → use context to resolve

--- EXAMPLES ---

Input:  1. It 's only just back there -- at least -- I 'm not sure .
Output: 1,"It 's only just back there -- at least -- I 'm not sure .",[]

Input:  2. This is the land of Narnia , said the Faun , where we are now ; all that lies between the lamp - post and the great castle of Cair Paravel on the eastern sea .
Output: 2,"This is the land of Narnia , said the Faun , where we are now ; all that lies between the lamp - post and the great castle of Cair Paravel on the eastern sea .","[{""text"": ""Faun"", ""canonical"": ""Mr. Tumnus"", ""label"": ""ACTIVE_SPEAKER""}]"

Input:  3. But the Faun continued sobbing as if his heart would break .
Output: 3,"But the Faun continued sobbing as if his heart would break .","[{""text"": ""Faun"", ""canonical"": ""Mr. Tumnus"", ""label"": ""ACTIVE_PERFORMER""}]"

Input:  4. He was a Faun .
Output: 4,"He was a Faun .","[{""text"": ""Faun"", ""canonical"": ""Mr. Tumnus"", ""label"": ""MENTIONED_ONLY""}]"

Input:  5. And when Lucy was tired of eating the Faun began to talk .
Output: 5,"And when Lucy was tired of eating the Faun began to talk .","[{""text"": ""Lucy"", ""canonical"": ""Lucy Pevensie"", ""label"": ""ACTIVE_THOUGHT""}, {""text"": ""Faun"", ""canonical"": ""Mr. Tumnus"", ""label"": ""ACTIVE_PERFORMER""}]"

Input:  6. You are the nicest Faun I 've ever met .
Output: 6,"You are the nicest Faun I 've ever met .","[{""text"": ""Faun"", ""canonical"": ""Mr. Tumnus"", ""label"": ""ADDRESSED""}]"

Input:  7. But I 've never seen a Son of Adam or a Daughter of Eve before .
Output: 7,"But I 've never seen a Son of Adam or a Daughter of Eve before .","[{""text"": ""Son of Adam"", ""canonical"": ""Son of Adam"", ""label"": ""MISCELLANEOUS""}, {""text"": ""Daughter of Eve"", ""canonical"": ""Daughter of Eve"", ""label"": ""MISCELLANEOUS""}]"

Input:  8. And may I ask , O Lucy , Daughter of Eve , said Mr. Tumnus , how you have come into Narnia ?
Output: 8,"And may I ask , O Lucy , Daughter of Eve , said Mr. Tumnus , how you have come into Narnia ?","[{""text"": ""Lucy"", ""canonical"": ""Lucy Pevensie"", ""label"": ""ADDRESSED""}, {""text"": ""Daughter of Eve"", ""canonical"": ""Lucy Pevensie"", ""label"": ""ADDRESSED""}, {""text"": ""Mr. Tumnus"", ""canonical"": ""Mr. Tumnus"", ""label"": ""ACTIVE_SPEAKER""}]"

Input:  9. Do n't go on talking like that , said Edmund .
Output: 9,"Do n't go on talking like that , said Edmund .","[{""text"": ""Edmund"", ""canonical"": ""Edmund Pevensie"", ""label"": ""ACTIVE_SPEAKER""}]"

--- DATA ---
[paste contents of chapters/chapter_N.txt here]
```
