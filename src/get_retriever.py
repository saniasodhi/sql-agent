"""
single shared retriever instance.

building a retriever embeds every table (~2s), so we do it once and reuse it
instead of rebuilding on each question.
"""

from src.retriever import SchemaRetriever

_retriever = None


def get_retriever(include_decoys: bool = True) -> SchemaRetriever:
    """Return a shared SchemaRetriever, building it on first call only."""
    global _retriever
    if _retriever is None:
        _retriever = SchemaRetriever(include_decoys=include_decoys)
    return _retriever