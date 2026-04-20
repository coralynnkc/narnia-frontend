## Experiment: GAP Batch 1 (End-to-End)

### Setup
- Dataset: GAP (converted to cluster format)
- Mode: End-to-End (mention detection + clustering)
- Model: ChatGPT (web interface)

### Results

| Metric | F1 |
|-------|----|
| MUC | 0.00 |
| B³ | 0.80 |
| CEAFₑ | 0.27 |
| CoNLL F1 | 0.36 |

### Key Finding

The model failed to produce meaningful coreference clusters,
defaulting to singleton predictions. This resulted in:

- zero MUC score (no links formed)
- inflated B³ score
- low CEAFₑ and CoNLL F1

### Interpretation

This demonstrates a systematic failure to perform cluster-based coreference,
despite correctly identifying mentions.
