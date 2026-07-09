"""Stage 2: CHUNK. Three strategies, token-based, over cleaned text."""

import re
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

_enc = tiktoken.get_encoding("cl100k_base")


def n_tokens(text: str) -> int:
    return len(_enc.encode(text))


def chunk_fixed(text: str, size: int = 300, overlap: int = 45) -> list[str]:
    """Blindly split every `size` tokens with overlap. Meaning-unaware."""
    toks = _enc.encode(text)
    chunks, step = [], size - overlap
    for start in range(0, len(toks), step):
        piece = toks[start : start + size]
        if piece:
            chunks.append(_enc.decode(piece))
    return chunks


def chunk_recursive(text: str, size: int = 300, overlap: int = 45) -> list[str]:
    """Split on paragraph -> sentence -> word boundaries, in priority order."""
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


def chunk_structure(text: str, max_size: int = 600) -> list[str]:
    """Split on contract structure: SECTION / ARTICLE / numbered headings.
    Falls back to recursive splitting for any oversized section."""
    # Split before lines that look like section/article headers
    pattern = re.compile(r"(?im)^(?=\s*(?:section|article)\s+\d+|\s*\d+\.\s+[A-Z])")
    parts = pattern.split(text)
    parts = [p.strip() for p in parts if p.strip()]
    chunks = []
    for part in parts:
        if n_tokens(part) <= max_size:
            chunks.append(part)
        else:
            # Section too big — sub-split it so no chunk is a giant wall
            chunks.extend(chunk_recursive(part, size=max_size, overlap=60))
    return chunks


if __name__ == "__main__":
    from pathlib import Path
    from loader import load_file

    files = sorted(Path("data/raw").glob("*.txt"))
    text = load_file(files[0])
    for name, fn in [
        ("FIXED", chunk_fixed),
        ("RECURSIVE", chunk_recursive),
        ("STRUCTURE", chunk_structure),
    ]:
        chunks = fn(text)
        sizes = [n_tokens(c) for c in chunks]
        avg = sum(sizes) // len(sizes) if sizes else 0
        print(
            f"{name:10} -> {len(chunks):3} chunks | avg {avg} tok | "
            f"min {min(sizes)} max {max(sizes)}"
        )
