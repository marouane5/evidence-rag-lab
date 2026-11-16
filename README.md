# Evidence RAG Lab

**A reproducible retrieval-and-grounding baseline for an AI engineering portfolio.**

Ask a question about a small English/French policy corpus, retrieve evidence with BM25, return a verbatim cited sentence, or abstain. Benchmark thresholds on development queries and evaluate on separate test queries. No API key, cloud service, LLM, embedding model or GPU is required.

This is an **AI-assisted initial portfolio implementation**, built and verified on 16 November 2026. It is an extractive retrieval baseline for a future RAG system, not a deployed LLM assistant. All Atlas policies are fictional demonstration content.

## Quick start

Python 3.10+; zero runtime dependencies. Run from the repository root:

```console
python -m unittest discover -s tests -v
python -m evidence_rag ask --query "How long are security audit events stored?"
python -m evidence_rag ask --query "À quoi sert une clé d'idempotence ?"
python -m evidence_rag benchmark
```

The benchmark writes `artifacts/benchmark.json`, including each query, ranked source IDs, extracted answer, citations, thresholds and corpus SHA-256. The CLI chooses thresholds from `data/development.jsonl`; the held-out test file is read only during benchmark evaluation.

## What is implemented

- Accent-insensitive English/French tokenization and deterministic BM25 scoring.
- Verbatim extractive answers with document ID, title, source URI and quoted evidence.
- Score/lexical-coverage abstention, selected by a 16-point development-set grid.
- Recall@3, MRR@3, answered-source accuracy, answer coverage and unanswerable abstention.
- Query-level development/test separation checks and corpus fingerprinting.
- Local `.md`/`.txt` directory ingestion with overlapping bounded chunks and citable relative source identifiers.
- Fourteen unit tests and a GitHub Actions workflow that reruns tests and the benchmark.

## Measured result

The checked-in run used **12 fictional documents, 10 development queries and 16 held-out test queries**. The test contains 12 answerable and 4 unanswerable queries:

| Metric | Observed result |
| --- | ---: |
| Retrieval Recall@3 | 1.000 |
| MRR@3 | 1.000 |
| Correct source among answered queries | 12/12 |
| Unanswerable questions correctly rejected | 4/4 |
| Overall answer coverage | 12/16 |

These are small, hand-authored demonstration results, **not evidence of production accuracy or generalization**. The held-out unit is the query; the corpus topics are shared between development and test. Source accuracy checks the cited document ID, not whether the extracted sentence actually answers the question.

A separate six-query **post-hoc challenge set** exposes the baseline's limitations: it rejects only 2/6 near-miss questions and incorrectly returns evidence for 4/6. For example, a backup-retention question gets backup frequency, and an application-log-encryption question gets log retention. See [known failures](docs/known-failures.md). These challenge cases were added after reviewing the baseline; they are diagnostic examples, not an untouched generalization test.

## Use your own corpus

Index a directory of UTF-8 Markdown/text files:

```console
python -m evidence_rag index --input my-documents --output artifacts/my-corpus.jsonl --chunk-words 160 --overlap 20
```

This preserves relative filenames and word ranges in `local://` source IDs, without embedding absolute workstation paths. The indexer does not parse PDF, HTML or Word files. Alternatively, create UTF-8 JSON Lines with one short, citable document per line:

```json
{"id":"runbook-1","title":"Backup policy","text":"Backups run every six hours.","source":"https://example.org/approved-policy","language":"en"}
```

Use unique IDs, nonempty text and a retrievable source. Split long material into bounded excerpts with distinct IDs and retain the original source link. Author labeled development and test query files using the included format, then run:

```console
python -m evidence_rag benchmark --corpus my-corpus.jsonl --development my-dev.jsonl --test my-test.jsonl --output artifacts/my-report.json
```

Keep test labels frozen after measuring results. For an honest next experiment, compare BM25 with an embedding retriever on a larger independently authored benchmark, and add contradiction and near-miss questions before introducing generation. The supplied development labels reference the demonstration corpus; when using another corpus, supply matching development/query labels rather than reusing those IDs.

## Design and limits

See [architecture](docs/architecture.md), [data card](docs/data-card.md) and [interview guide](docs/interview-guide.md). This system matches words; it does not translate queries or perform semantic multilingual retrieval. Documents are treated as data and never executed, but retrieved malicious text can still be quoted. There is no authentication, privacy filtering, enterprise compliance, streaming API or generative answer model.

**Résumé en français :** prototype local de recherche de preuves avec BM25, citations, abstention et évaluation sur des requêtes séparées. Corpus bilingue fictif, sans LLM ni service externe. Les scores concernent uniquement ce petit jeu de démonstration.

MIT licensed. The included fictional corpus and queries are original demonstration material released under the same license.
