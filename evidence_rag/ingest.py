"""Turn user-selected local Markdown/text documents into bounded citable records."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import quote


def index_directory(directory: str | Path, output: str | Path, chunk_words: int = 160, overlap: int = 20) -> dict:
    root = Path(directory)
    if not root.is_dir():
        raise ValueError("Input must be a directory containing UTF-8 .md or .txt files")
    if chunk_words < 30 or overlap < 0 or overlap >= chunk_words:
        raise ValueError("Use chunk_words >= 30 and 0 <= overlap < chunk_words")
    records, files = [], 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.casefold() not in (".md", ".txt"):
            continue
        text = path.read_text(encoding="utf-8")
        words = text.split()
        if not words:
            continue
        files += 1
        relative = path.relative_to(root).as_posix()
        file_id = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:12]
        for number, start in enumerate(range(0, len(words), chunk_words - overlap)):
            excerpt = " ".join(words[start:start + chunk_words])
            records.append({"id": f"local-{file_id}-{number:04}", "title": f"{relative} (chunk {number + 1})",
                            "text": excerpt, "source": "local://" + quote(relative) + f"#words-{start}-{min(start + chunk_words, len(words))}",
                            "language": "und"})
            if start + chunk_words >= len(words):
                break
    if not records:
        raise ValueError("No nonempty UTF-8 Markdown/text documents found")
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
    return {"files_indexed": files, "chunks": len(records), "chunk_words": chunk_words, "overlap_words": overlap, "output": str(output)}
