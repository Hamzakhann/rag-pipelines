"""Diagnostic: is the Nelnet contract loading and chunking correctly?"""
import sys
sys.path.insert(0, "src")
from pathlib import Path
from loader import load_file
from chunkers import chunk_structure

files = [f for f in Path("data/raw").glob("*.txt") if "NELNET" in f.name.upper()]

if not files:
    print("❌ Nelnet file is NOT in data/raw/ — it never downloaded!")
else:
    f = files[0]
    text = load_file(f)
    chunks = chunk_structure(text)
    print(f"File: {f.name}")
    print(f"Loaded text length: {len(text)} chars")
    print(f"Number of chunks produced: {len(chunks)}")
    for i, c in enumerate(chunks):
        preview = repr(c[:80])
        print(f"  chunk {i}: {len(c)} chars — {preview}")
