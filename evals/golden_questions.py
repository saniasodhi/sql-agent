"""
Day 7 golden dataset.

A small set of natural-language questions for the Chinook database, each paired
with a known-correct SQL query (the "gold" query). We run the agent on every
question, execute both the agent's SQL and the gold SQL, and check if their
results match.

This is small (10 questions) on purpose — small enough to debug each failure
by hand, big enough to give a meaningful percentage. We'll grow it later.
"""

# Each entry: a question (what the user asks) and a gold SQL query
# (a known-correct way to answer it). The agent's SQL doesn't have to MATCH
# this string — it just has to produce the same results when executed.
GOLDEN_QUESTIONS = [
    {
        "id": 1,
        "question": "How many artists are in the database?",
        "gold_sql": "SELECT COUNT(*) AS count FROM Artist;",
        "difficulty": "easy",
    },
    {
        "id": 2,
        "question": "List the names of the first 5 artists alphabetically.",
        "gold_sql": "SELECT Name FROM Artist ORDER BY Name LIMIT 5;",
        "difficulty": "easy",
    },
    {
        "id": 3,
        "question": "How many tracks are in the database?",
        "gold_sql": "SELECT COUNT(*) AS count FROM Track;",
        "difficulty": "easy",
    },
    {
        "id": 4,
        "question": "What are the top 3 genres by number of tracks?",
        "gold_sql": """
            SELECT g.Name, COUNT(t.TrackId) AS track_count
            FROM Genre g
            JOIN Track t ON g.GenreId = t.GenreId
            GROUP BY g.GenreId
            ORDER BY track_count DESC
            LIMIT 3;
        """,
        "difficulty": "medium",
    },
    {
        "id": 5,
        "question": "Which 3 customers spent the most money in total?",
        "gold_sql": """
            SELECT c.FirstName, c.LastName, SUM(i.Total) AS total_spent
            FROM Customer c
            JOIN Invoice i ON c.CustomerId = i.CustomerId
            GROUP BY c.CustomerId
            ORDER BY total_spent DESC
            LIMIT 3;
        """,
        "difficulty": "medium",
    },
    {
        "id": 6,
        "question": "How many invoices were issued to customers in Germany?",
        "gold_sql": """
            SELECT COUNT(*) AS count
            FROM Invoice
            WHERE BillingCountry = 'Germany';
        """,
        "difficulty": "easy",
    },
    {
        "id": 7,
        "question": "What is the name of the longest track in the database?",
        "gold_sql": """
            SELECT Name
            FROM Track
            ORDER BY Milliseconds DESC
            LIMIT 1;
        """,
        "difficulty": "medium",
    },
    {
        "id": 8,
        "question": "List the 5 albums with the most tracks. Show album title and number of tracks.",
        "gold_sql": """
            SELECT al.Title, COUNT(t.TrackId) AS track_count
            FROM Album al
            JOIN Track t ON al.AlbumId = t.AlbumId
            GROUP BY al.AlbumId
            ORDER BY track_count DESC
            LIMIT 5;
        """,
        "difficulty": "medium",
    },
    {
        "id": 9,
        "question": "Which artist has the most albums? Show the artist name and the album count.",
        "gold_sql": """
            SELECT ar.Name, COUNT(al.AlbumId) AS album_count
            FROM Artist ar
            JOIN Album al ON ar.ArtistId = al.ArtistId
            GROUP BY ar.ArtistId
            ORDER BY album_count DESC
            LIMIT 1;
        """,
        "difficulty": "medium",
    },
    {
        "id": 10,
        "question": "What is the total revenue from customers in the USA?",
        "gold_sql": """
            SELECT SUM(i.Total) AS total_revenue
            FROM Invoice i
            WHERE i.BillingCountry = 'USA';
        """,
        "difficulty": "medium",
    },
]