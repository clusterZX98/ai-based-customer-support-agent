from pathlib import Path

KNOWLEDGE_BASE_DIR = Path("knowledge_base")


def search_knowledge_base(query: str) -> str:
    """
    Simple keyword-matching search over the knowledge_base/*.txt files.

    This is intentionally simple. Later this can be upgraded to:
    Documents -> Chunking -> Embeddings -> Vector DB -> Semantic Retrieval
    """
    if not query:
        return "No relevant knowledge-base information was found."

    query_words = [
        word.strip(".,?!:;\"'")
        for word in query.lower().split()
        if len(word.strip(".,?!:;\"'")) > 2
    ]

    if not query_words:
        return "No relevant knowledge-base information was found."

    results = []

    for file_path in KNOWLEDGE_BASE_DIR.glob("*.txt"):
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            continue

        content_lower = content.lower()
        score = sum(1 for word in query_words if word in content_lower)

        if score > 0:
            results.append((score, file_path.name, content))

    results.sort(key=lambda x: x[0], reverse=True)

    if not results:
        return "No relevant knowledge-base information was found."

    top_results = results[:3]

    formatted = []
    for score, filename, content in top_results:
        formatted.append(f"--- {filename} ---\n{content}")

    return "\n\n".join(formatted)