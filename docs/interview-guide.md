# Candidate review and extension guide

This project was created with AI assistance. Before discussing it as your work, run it, inspect each module, explain the choices below and implement an extension you can defend.

1. **Trace a question:** `ask` loads documents, builds the lexical index, tunes thresholds on development questions, retrieves candidates and returns a verbatim sentence with its source.
2. **Explain BM25:** repeated terms saturate; document length is normalized; rare query terms receive greater weight. Explain why a lexical baseline is useful before paying for embeddings.
3. **Distinguish retrieval and generation:** this implementation performs no LLM inference. Adding a generator introduces hallucination, latency, cost and prompt-injection evaluation questions.
4. **Explain abstention:** the threshold is chosen without test labels; score and coverage are heuristic signals, not calibrated confidence probabilities.
5. **Read the failures honestly:** the current tiny set is easy. Design near-miss questions with shared terms, conflicting policy revisions, irrelevant pasted instructions and genuine cross-language queries. Report the new performance even if it is lower.
6. **Discuss metrics:** perfect Recall@3 can coexist with a wrong first citation; high answer accuracy can coexist with low coverage; correctly quoting a source does not prove its truth.

Suggested next contribution: add a version-aware corpus with effective dates, implement revision filtering, and write a test proving an obsolete policy can never be cited for a current-date query. Then compare the same frozen benchmark with a semantic retriever.
