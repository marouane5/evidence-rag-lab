# Known failure cases: topical retrieval is not answerability

The initial sixteen-query fixture is deliberately small and easy. An independent review tested harder questions that share policy vocabulary but ask for facts absent from the corpus. These exposed a real limitation: the highest-scoring relevant-looking document may not contain an answer to the exact question.

Reproduce the six diagnostic cases without changing thresholds:

```console
python -m evidence_rag benchmark --test data/challenge.jsonl --output artifacts/challenge.json
```

Observed on the same corpus and development thresholds: **2/6 correct abstentions, 4/6 unsupported answers**. No thresholds were retuned using this challenge set. It is a post-hoc diagnostic set, not an independent held-out test.

| Question | Returned evidence | Why it is wrong as an answer |
| --- | --- | --- |
| How long are database backups retained? | Encrypted database backups run every six hours. | Backup frequency does not state retention. |
| Does Atlas encrypt application logs? | Operational application logs are retained for 14 days. | Retention says nothing about encryption. |

BM25 retrieves topical lexical overlap. The answer extractor returns a source sentence verbatim, so it cannot invent new wording, but **a true quote can still answer the wrong question**. The field `answer_source_accuracy` only checks whether the cited document is in the query's relevance labels; it does not judge entailment, completeness or factual truth.

The present interface should be treated as an evidence-candidate search tool. Stronger answerability checks, adversarial negatives, contradiction handling and human evaluation are required before treating it as an autonomous question-answering service. Adding an LLM would require a separate benchmark and would not by itself resolve this limitation.
