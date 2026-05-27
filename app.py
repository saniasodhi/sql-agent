"""
streamlit web UI for the sql-agent.

type a question -> see retrieved tables -> generated SQL -> results table.
run with:  streamlit run app.py
"""

import pandas as pd
import streamlit as st

from src.agent import text_to_sql
from src.get_retriever import get_retriever


# ---- page setup ----
st.set_page_config(page_title="SQL-Agent", page_icon="🗄️", layout="wide")

# a little custom styling
st.markdown("""
<style>
    .stButton button { font-size: 0.85rem; }
    code { font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

col_title, col_meta = st.columns([3, 1])
with col_title:
    st.title("🗄️ SQL-Agent")
    st.caption("natural language → SQL → answer. retrieves relevant tables, writes SQL, self-corrects, runs it.")
with col_meta:
    st.markdown("")
    st.markdown("")
    st.markdown(
        "<div style='text-align:right; color:gray; font-size:0.8rem;'>"
        "haiku 4.5 · RAG retrieval · sqlite<br>"
        "<a href='https://github.com/saniasodhi/sql-agent'>github →</a>"
        "</div>",
        unsafe_allow_html=True,
    )

with st.expander("how it works"):
    st.markdown("""
    1. **retrieve** — embeds your question and finds the most relevant database tables (out of 41, incl. decoys)
    2. **generate** — sends only those tables + your question to the model, gets a SQL draft
    3. **self-critique** — the model reviews its own SQL for mistakes before running
    4. **execute** — runs the SQL; if it errors, feeds the error back and retries (up to 3x)
    5. **show** — displays the tables it picked, the final SQL, and the results
    """)


# ---- cached retriever ----
# st.cache_resource keeps the retriever alive across reruns (streamlit reruns
# the whole script on every interaction, so without caching we'd rebuild it each time).
@st.cache_resource
def load_retriever():
    return get_retriever(include_decoys=True)

retriever = load_retriever()
# warm-up note shown only until the first query
if "has_run" not in st.session_state:
    st.session_state.has_run = False

# ---- example questions (clickable) ----
EXAMPLES = [
    "Which 3 customers spent the most money?",
    "What are the top 5 genres by number of tracks?",
    "What is the longest track in the database?",
    "How much total revenue came from customers in the USA?",
    "Which employee has handled the most customers?",
]

st.subheader("try an example or type your own")

# show examples as buttons in a row
cols = st.columns(len(EXAMPLES))
clicked_example = None
for col, ex in zip(cols, EXAMPLES):
    if col.button(ex, use_container_width=True):
        clicked_example = ex

# text box (pre-filled if an example was clicked)
question = st.text_input(
    "your question",
    value=clicked_example or "",
    placeholder="e.g. which artist has the most albums?",
)

run = st.button("run", type="primary")


# ---- run the agent ----
if run and question.strip():
    with st.spinner("retrieving tables, writing SQL, running it..."):
        result = text_to_sql(question, retriever=retriever, top_k=8)

    # layout: two columns — left = SQL + tables, right = results
    left, right = st.columns([1, 1])

    with left:
        st.markdown("**retrieved tables**")
        tables = result.get("schema_tables")
        if tables:
            st.write(", ".join(tables))
        else:
            st.write("_(used full schema)_")

        st.markdown("**generated SQL**")
        st.code(result["sql"], language="sql")

        st.markdown("**details**")
        st.write(f"attempts: {result['attempts']}  |  critic: {result.get('critic_action')}")

    with right:
        st.markdown("**results**")
        if result["sql"].strip().startswith("-- UNANSWERABLE"):
            st.info("i can only answer questions about the music store database (artists, albums, tracks, customers, invoices, etc). try one of those.")
        elif result["error"]:
            st.error(result["error"])
        elif result["results"]:
            df = pd.DataFrame(result["results"])
            st.dataframe(df, use_container_width=True)
            st.caption(f"{len(result['results'])} row(s)")
        else:
            st.info("query ran but returned no rows.")

elif run:
    st.warning("type a question first.")


# ---- footer ----
st.divider()
st.caption("built with claude (haiku 4.5) + sentence-transformers retrieval + sqlite (chinook db). github.com/saniasodhi/sql-agent")