"""BM25, extractive answers, and citations. No model/API dependency is required."""
from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

STOP = set("a an the and or is are was were to of in on for by with this that can how what which do does when who it its at as be from about has have i we you your our all not if than et ou le la les un une des du de d en est sont pour par avec ce cette ces quel quelle quels quelles comment quand qui quoi au aux sur dans se a il elle on nous vous leur son sa ses que peut doit".split())


def tokens(text: str) -> list[str]:
    """Accent-insensitive lexical tokens; no cross-language semantic inference."""
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return [t for t in re.findall(r"[a-z0-9]+", text) if t not in STOP and len(t) > 1]


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    text: str
    source: str
    language: str


def load_documents(path: str | Path) -> list[Document]:
    documents = [Document(**json.loads(line)) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [d.id for d in documents]
    if not documents or len(ids) != len(set(ids)):
        raise ValueError("Corpus must be nonempty and document IDs unique")
    for d in documents:
        if not d.text.strip() or not d.source.strip():
            raise ValueError("Every document needs nonempty text and a source")
    return documents


class Retriever:
    """One bounded document per index entry; BM25 is deterministic and inspectable."""

    def __init__(self, documents: list[Document], k1: float = 1.5, b: float = 0.75):
        if not documents or len({d.id for d in documents}) != len(documents):
            raise ValueError("Provide nonempty documents with unique IDs")
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("Invalid BM25 parameters")
        self.documents = documents
        self.k1, self.b = k1, b
        self.tf = [Counter(tokens(d.title + " " + d.text)) for d in documents]
        self.lengths = [sum(t.values()) for t in self.tf]
        self.avgdl = sum(self.lengths) / len(documents) or 1
        self.df = Counter(t for tf in self.tf for t in tf)
        self.fingerprint = hashlib.sha256(json.dumps([d.__dict__ for d in documents], sort_keys=True).encode()).hexdigest()

    def search(self, query: str, k: int = 3) -> list[dict]:
        if k < 1:
            raise ValueError("k must be positive")
        qt = set(tokens(query))
        ranked = []
        for doc, tf, dl in zip(self.documents, self.tf, self.lengths):
            score = 0.0
            for term in qt:
                f = tf[term]
                if not f:
                    continue
                idf = math.log(1 + (len(self.documents) - self.df[term] + 0.5) / (self.df[term] + 0.5))
                score += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            if score > 0:
                ranked.append({"document": doc, "score": score, "coverage": len(qt.intersection(tf)) / max(1, len(qt))})
        ranked.sort(key=lambda r: (-r["score"], r["document"].id))
        return ranked[:k]

    def answer(self, query: str, min_score: float = 2.0, min_coverage: float = 0.35, k: int = 3) -> dict:
        hits = self.search(query, k)
        common = {"query": query, "corpus_sha256": self.fingerprint, "method": "extractive_bm25", "generation": False}
        public_hits = [{"id": h["document"].id, "score": round(h["score"], 4), "coverage": round(h["coverage"], 4)} for h in hits]
        if not hits or hits[0]["score"] < min_score or hits[0]["coverage"] < min_coverage:
            return {**common, "abstained": True, "answer": "Insufficient evidence in the indexed corpus.", "citations": [], "retrieval": public_hits}
        doc = hits[0]["document"]
        sentences = re.split(r"(?<=[.!?])\s+", doc.text.strip())
        qt = set(tokens(query))
        # Return verbatim source text. Prompt-like content is never executed.
        sentence = max(sentences, key=lambda s: len(qt.intersection(tokens(s))))
        return {**common, "abstained": False, "answer": sentence, "citations": [{"id": doc.id, "title": doc.title, "source": doc.source, "quote": sentence}], "retrieval": public_hits}


def evaluate(retriever: Retriever, queries: list[dict], config: dict) -> dict:
    if not queries:
        raise ValueError("Evaluation queries are empty")
    records, recalls, reciprocal = [], [], []
    confusion = {"answerable_answered": 0, "answerable_abstained": 0, "unanswerable_answered": 0, "unanswerable_abstained": 0}
    for row in queries:
        expected = set(row["relevant_ids"])
        result = retriever.answer(row["query"], **config)
        retrieved = [h["id"] for h in result["retrieval"]]
        if expected:
            recalls.append(len(expected.intersection(retrieved)) / len(expected))
            reciprocal.append(next((1 / rank for rank, docid in enumerate(retrieved, 1) if docid in expected), 0.0))
        key = ("answerable" if expected else "unanswerable") + ("_abstained" if result["abstained"] else "_answered")
        confusion[key] += 1
        records.append({"id": row["id"], "expected_ids": sorted(expected), **result})
    answered = [r for r in records if not r["abstained"]]
    correct_answered = sum(bool(set(r["expected_ids"]).intersection(c["id"] for c in r["citations"])) for r in answered)
    answerable = confusion["answerable_answered"] + confusion["answerable_abstained"]
    unanswerable = confusion["unanswerable_answered"] + confusion["unanswerable_abstained"]
    return {"n_queries": len(queries), "n_answerable": answerable, "n_unanswerable": unanswerable, "recall_at_3": sum(recalls) / len(recalls) if recalls else None,
            "mrr_at_3": sum(reciprocal) / len(reciprocal) if reciprocal else None,
            "answer_source_accuracy": correct_answered / len(answered) if answered else None,
            "answer_coverage": len(answered) / len(records),
            "unanswerable_abstention_rate": confusion["unanswerable_abstained"] / unanswerable if unanswerable else None,
            "confusion": confusion, "config": config, "corpus_sha256": retriever.fingerprint, "records": records}


def read_queries(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def tune(retriever: Retriever, development: list[dict]) -> dict:
    """Thresholds selected on development queries only, never test labels."""
    best = None
    for score in (1.0, 2.0, 3.0, 4.0):
        for coverage in (0.25, 0.35, 0.5, 0.65):
            config = {"min_score": score, "min_coverage": coverage}
            report = evaluate(retriever, development, config)
            good = sum((not r["abstained"] and r["citations"][0]["id"] in r["expected_ids"]) or (r["abstained"] and not r["expected_ids"]) for r in report["records"])
            candidate = (good / len(development), coverage, score)
            if best is None or candidate > best[0]:
                best = (candidate, config)
    return best[1]
