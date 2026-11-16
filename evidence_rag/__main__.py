import argparse
import json
from pathlib import Path

from .core import Retriever, evaluate, load_documents, read_queries, tune
from .ingest import index_directory


def main():
    parser = argparse.ArgumentParser(description="Local cited evidence retrieval and query-level benchmark")
    parser.add_argument("command", choices=["ask", "benchmark", "index"])
    parser.add_argument("--corpus", default="data/corpus.jsonl")
    parser.add_argument("--query")
    parser.add_argument("--development", default="data/development.jsonl")
    parser.add_argument("--test", default="data/test.jsonl")
    parser.add_argument("--output")
    parser.add_argument("--input", help="Directory of UTF-8 .md/.txt files for index")
    parser.add_argument("--chunk-words", type=int, default=160)
    parser.add_argument("--overlap", type=int, default=20)
    args = parser.parse_args()
    if args.command == "index":
        if not args.input:
            parser.error("index requires --input")
        print(json.dumps(index_directory(args.input, args.output or "artifacts/corpus.jsonl", args.chunk_words, args.overlap), indent=2))
        return
    retriever = Retriever(load_documents(args.corpus))
    development = read_queries(args.development)
    config = tune(retriever, development)
    if args.command == "ask":
        if not args.query:
            parser.error("ask requires --query")
        print(json.dumps(retriever.answer(args.query, **config), indent=2, ensure_ascii=False))
        return
    test = read_queries(args.test)
    if {r["id"] for r in development}.intersection(r["id"] for r in test) or {r["query"].casefold() for r in development}.intersection(r["query"].casefold() for r in test):
        raise ValueError("Development/test query overlap")
    report = evaluate(retriever, test, config)
    report["threshold_selection"] = {"split": "development", "n_queries": len(development), "method": "16-point grid; maximize correct source or correct abstention"}
    output = Path(args.output or "artifacts/benchmark.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
