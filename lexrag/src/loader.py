"""Stage 1: LOAD. Turn a raw contract file into clean plain text."""

import re
import sys
from pathlib import Path


def clean_text(text: str) -> str:
    """Normalize whitespace and strip common PDF boilerplate."""
    # Drop page markers like "Page 1 of 40" / "- 12 -"
    text = re.sub(r"(?im)^\s*page\s+\d+\s+of\s+\d+\s*$", "", text)
    text = re.sub(r"(?m)^\s*-\s*\d+\s*-\s*$", "", text)
    # Collapse 3+ newlines into a paragraph break
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse runs of spaces/tabs
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Strip trailing spaces per line
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def load_file(path: Path) -> str:
    """Load .txt or .pdf into cleaned text. Errors go to stderr."""
    try:
        if path.suffix.lower() == ".pdf":
            import pdfplumber

            parts = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    parts.append(page.extract_text() or "")
            raw = "\n".join(parts)
        else:
            raw = path.read_text(encoding="utf-8", errors="replace")
        return clean_text(raw)
    except Exception as e:
        print(f"SKIP: could not load {path.name} — {e}", file=sys.stderr)
        return ""


if __name__ == "__main__":
    # Demo: load first raw file and print a preview
    raw_dir = Path("data/raw")
    files = sorted(f for f in raw_dir.iterdir() if f.suffix.lower() in {".txt", ".pdf"})
    if not files:
        print("No files in data/raw/. Run src/download_data.py first.", file=sys.stderr)
        sys.exit(1)
    text = load_file(files[0])
    print(f"--- {files[0].name} ---")
    print(f"Length: {len(text)} chars\n")
    print(text[:800])
