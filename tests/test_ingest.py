import tempfile
import unittest
from pathlib import Path

from evidence_rag.core import load_documents
from evidence_rag.ingest import index_directory


class IngestTests(unittest.TestCase):
    def test_chunk_bounds_sources_and_determinism(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            (source / "policy.md").write_text(" ".join(f"word{i}" for i in range(100)), encoding="utf-8")
            output = root / "corpus.jsonl"
            report = index_directory(source, output, chunk_words=40, overlap=10)
            first = output.read_text(encoding="utf-8")
            docs = load_documents(output)
            self.assertEqual(report["chunks"], 3)
            self.assertTrue(all(len(d.text.split()) <= 40 for d in docs))
            self.assertTrue(all(d.source.startswith("local://policy.md#words-") for d in docs))
            index_directory(source, output, chunk_words=40, overlap=10)
            self.assertEqual(first, output.read_text(encoding="utf-8"))
            self.assertIn("word30", docs[0].text)
            self.assertTrue(docs[1].text.startswith("word30 "))

    def test_empty_directory_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                index_directory(temp, Path(temp) / "out.jsonl")

    def test_invalid_overlap_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                index_directory(temp, Path(temp) / "out.jsonl", chunk_words=40, overlap=40)


if __name__ == "__main__":
    unittest.main()
