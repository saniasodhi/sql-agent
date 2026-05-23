"""
schema retriever using embeddings.

given a question, returns the most relevant tables from the (possibly huge)
database schema. this is RAG applied to schemas: embed each table once,
embed the question, return the tables whose embeddings are most similar.
"""

from sentence_transformers import SentenceTransformer, util
from src.schema_tools import get_all_table_schemas


# small, fast, good-quality embedding model. downloads ~90MB the first time.
_MODEL_NAME = "all-MiniLM-L6-v2"
_model = None  # loaded lazily so importing this file is cheap


def _get_model():
    """Load the embedding model once and reuse it."""
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def _table_to_text(name: str, create_sql: str) -> str:
    """
    Turn a table into a short text blob for embedding.
    We use the table name + its CREATE statement so column names
    contribute to the meaning.
    """
    return f"Table {name}: {create_sql}"


class SchemaRetriever:
    """
    Embeds all tables upfront, then retrieves the top-k most relevant
    tables for a given question.
    """

    def __init__(self, include_decoys: bool = True):
        self.schemas = get_all_table_schemas(include_decoys=include_decoys)
        self.table_names = list(self.schemas.keys())

        # build the text blob for each table
        texts = [_table_to_text(n, self.schemas[n]) for n in self.table_names]

        # embed all tables once. convert_to_tensor lets us use fast similarity.
        model = _get_model()
        self.table_embeddings = model.encode(texts, convert_to_tensor=True)

    def retrieve(self, question: str, top_k: int = 5) -> list[str]:
        """
        Return the names of the top_k most relevant tables for the question.
        """
        model = _get_model()
        q_emb = model.encode(question, convert_to_tensor=True)

        # cosine similarity between the question and every table
        scores = util.cos_sim(q_emb, self.table_embeddings)[0]

        # pair each table with its score, sort high to low
        ranked = sorted(
            zip(self.table_names, scores.tolist()),
            key=lambda x: x[1],
            reverse=True,
        )
        return [name for name, score in ranked[:top_k]]

    def retrieve_schema_string(self, question: str, top_k: int = 5) -> str:
        """
        Return the CREATE statements for just the top_k relevant tables,
        ready to drop into a prompt.
        """
        names = self.retrieve(question, top_k=top_k)
        return "\n\n".join(self.schemas[n] for n in names)


if __name__ == "__main__":
    # quick test: does it pick sensible tables?
    print("loading model + embedding tables (first run downloads ~90MB)...")
    retriever = SchemaRetriever(include_decoys=True)
    print(f"indexed {len(retriever.table_names)} tables\n")

    test_questions = [
        "Which 3 customers spent the most money?",
        "What are the top genres by number of tracks?",
        "List all employees who report to Nancy Edwards.",
    ]

    for q in test_questions:
        tables = retriever.retrieve(q, top_k=5)
        print(f"Q: {q}")
        print(f"   top 5 tables: {tables}\n")