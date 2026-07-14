"""Stage 5: GENERATE. Full naive RAG — retrieve, then answer with citation."""
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"   # ← MUST be first, before imports that load tokenizers
import sys
from dotenv import load_dotenv
import anthropic
from retrieve import retrieve

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

os.environ["TOKENIZERS_PARALLELISM"] = "false"

PROMPT_TEMPLATE = """You are a contract analysis assistant. Answer the question \
using ONLY the context below. If the answer is not in the context, say \
"I could not find this in the provided contracts." Cite the contract name(s) you used.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

def answer(question: str, k: int = 4) -> str:
    chunks = retrieve(question, k=k)
    context = "\n\n---\n\n".join(
        f"[From: {c['contract']}]\n{c['text']}" for c in chunks
    )
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "What is the governing law?"
    print(f"QUESTION: {q}\n" + "=" * 60)
    print(answer(q))
