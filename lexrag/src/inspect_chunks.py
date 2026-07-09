"""The chunk-inspection drill: does a chunk hold the answer INTACT?"""
print("Inspecting chunks for intactness of answers...")
import sys
from pathlib import Path
from loader import load_file
from chunkers import chunk_fixed, chunk_recursive, chunk_structure, n_tokens


def find_phrase(chunks: list[str], phrase: str):
    hits = [(i, c) for i, c in enumerate(chunks) if phrase.lower() in c.lower()]
    return hits


if __name__ == "__main__":
    phrase = sys.argv[1] if len(sys.argv) > 1 else "termination"
    files = sorted(Path("data/raw").glob("*.txt"))
    text = load_file(files[0])
    print(f"Contract: {files[0].name}")
    print(f"Searching for: '{phrase}'\n" + "=" * 60)

    for name, fn in [
        ("FIXED", chunk_fixed),
        ("RECURSIVE", chunk_recursive),
        ("STRUCTURE", chunk_structure),
    ]:
        chunks = fn(text)
        hits = find_phrase(chunks, phrase)
        print(f"\n### {name}: {len(hits)} chunk(s) contain '{phrase}'")
        if hits:
            i, c = hits[0]
            print(f"    First hit = chunk #{i}, size {n_tokens(c)} tokens")
            # Show the chunk so you can judge: intact? or severed/noisy?
            print("    --- chunk preview ---")
            print("    " + c[:1000].replace("\n", "\n    "))
