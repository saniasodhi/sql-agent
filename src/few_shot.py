"""
Few-shot examples for the SQL-Agent prompt.

These are HAND-PICKED to teach the model:
  1. SQL style (lowercase keywords, table aliases, semicolons)
  2. Common patterns it'll see in the eval (joins, aggregates, filters)
  3. How to handle multi-table joins (the trickiest case)

CRITICAL: None of these questions appear in the eval golden dataset.
Using eval questions as examples would be a form of test contamination.
"""

# Each example is a (question, SQL) pair.
# We include 4 examples, each demonstrating a different pattern.
FEW_SHOT_EXAMPLES = [
    {
        # Pattern 1: simple count, no joins.
        "question": "How many albums are in the database?",
        "sql": "SELECT COUNT(*) AS album_count FROM Album;",
    },
    {
        # Pattern 2: filter + count.
        "question": "How many tracks are longer than 5 minutes?",
        "sql": "SELECT COUNT(*) AS count FROM Track WHERE Milliseconds > 300000;",
    },
    {
        # Pattern 3: two-table join + aggregate + group + order + limit.
        # This is the most common analytics pattern.
        "question": "Which 3 artists have the most albums?",
        "sql": (
            "SELECT ar.Name, COUNT(al.AlbumId) AS album_count "
            "FROM Artist ar "
            "JOIN Album al ON ar.ArtistId = al.ArtistId "
            "GROUP BY ar.ArtistId "
            "ORDER BY album_count DESC "
            "LIMIT 3;"
        ),
    },
    {
        # Pattern 4: three-table join — Track -> Album -> Artist.
        # Teaches the model how to chain joins along foreign keys.
        "question": "What is the average track length per artist? Show the top 5 artists by average length.",
        "sql": (
            "SELECT ar.Name, AVG(t.Milliseconds) AS avg_ms "
            "FROM Artist ar "
            "JOIN Album al ON ar.ArtistId = al.ArtistId "
            "JOIN Track t ON al.AlbumId = t.AlbumId "
            "GROUP BY ar.ArtistId "
            "ORDER BY avg_ms DESC "
            "LIMIT 5;"
        ),
    },
]


def format_few_shot_block() -> str:
    """
    Render the examples as a string ready to inject into the system prompt.
    Returns an empty string if there are no examples.
    """
    if not FEW_SHOT_EXAMPLES:
        return ""

    lines = ["EXAMPLES:\n"]
    for i, ex in enumerate(FEW_SHOT_EXAMPLES, 1):
        lines.append(f"Example {i}:")
        lines.append(f"Q: {ex['question']}")
        lines.append(f"A: {ex['sql']}")
        lines.append("")  # blank line between examples
    return "\n".join(lines)


if __name__ == "__main__":
    # Quick sanity check.
    print(format_few_shot_block())