import os
from pathlib import Path

# Avoid importing heavy/possibly incompatible langchain modules at import-time
# because the versions can conflict during testing or when the package is not
# needed.  The functions below import lazily.

CORPUS_DIR = Path("data/corpus")
INDEX_PATH = Path("data/faiss_index")

def build_or_load_index() -> "FAISS":
    # deferred imports inside function body to avoid import-time errors
    from langchain_community.vectorstores import FAISS
    # prefer community embeddings package; fall back to langchain.embeddings
    try:
        from langchain_community.embeddings import OpenAIEmbeddings
    except Exception:
        try:
            from langchain.embeddings import OpenAIEmbeddings
        except Exception:
            # last resort: langchain_openai (may import langchain_core and fail)
            from langchain_openai import OpenAIEmbeddings

    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    # propagate whichever API key is set so downstream libraries see it
    from analyst.utils import ensure_api_key
    ensure_api_key()

    embeddings = OpenAIEmbeddings()
    if INDEX_PATH.exists():
        return FAISS.load_local(str(INDEX_PATH), embeddings,
                                allow_dangerous_deserialization=True)

    docs = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)

    for f in CORPUS_DIR.glob("**/*"):
        if f.suffix == ".pdf":
            loader = PyPDFLoader(str(f))
        elif f.suffix in {".txt", ".md"}:
            loader = TextLoader(str(f))
        else:
            continue
        docs.extend(splitter.split_documents(loader.load()))

    if not docs:
        return None

    store = FAISS.from_documents(docs, embeddings)
    store.save_local(str(INDEX_PATH))
    return store


def retrieve_context(query: str, k: int = 6) -> tuple[str, list[dict]]:
    store = build_or_load_index()
    if store is None:
        return "", []

    results = store.similarity_search_with_score(query, k=k)
    sources = []
    chunks = []

    for doc, score in results:
        chunks.append(doc.page_content)
        # FAISS L2 scores are squared distances and can exceed 1.0, so clamp
        # the derived relevance to [0.0, 1.0] to avoid negative display values.
        relevance = round(max(0.0, min(1.0, 1.0 - score)), 3)
        sources.append({
            "source": doc.metadata.get("source", "Unknown"),
            "page":   doc.metadata.get("page", "—"),
            "relevance": relevance,
        })

    return "\n\n".join(chunks), sources
