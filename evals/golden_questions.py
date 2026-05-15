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
    {
        "id": 11,
        "question": "How many invoices were issued in 2010?",
        "gold_sql": "SELECT COUNT(*) AS count FROM Invoice WHERE InvoiceDate LIKE '2010%';",
        "difficulty": "easy",
    },
    {
        "id": 12,
        "question": "What is the average invoice total?",
        "gold_sql": "SELECT AVG(Total) AS avg_total FROM Invoice;",
        "difficulty": "easy",
    },
    {
        "id": 13,
        "question": "Which country has the most customers?",
        "gold_sql": (
            "SELECT Country, COUNT(*) AS customer_count "
            "FROM Customer GROUP BY Country "
            "ORDER BY customer_count DESC LIMIT 1;"
        ),
        "difficulty": "easy",
    },
    {
        "id": 14,
        "question": "List all employees who report to Nancy Edwards.",
        "gold_sql": (
            "SELECT e.FirstName, e.LastName FROM Employee e "
            "JOIN Employee m ON e.ReportsTo = m.EmployeeId "
            "WHERE m.FirstName = 'Nancy' AND m.LastName = 'Edwards';"
        ),
        "difficulty": "hard",
    },
    {
        "id": 15,
        "question": "What is the total revenue per genre? Show the top 5.",
        "gold_sql": (
            "SELECT g.Name, SUM(il.UnitPrice * il.Quantity) AS revenue "
            "FROM Genre g "
            "JOIN Track t ON g.GenreId = t.GenreId "
            "JOIN InvoiceLine il ON t.TrackId = il.TrackId "
            "GROUP BY g.GenreId ORDER BY revenue DESC LIMIT 5;"
        ),
        "difficulty": "hard",
    },
    {
        "id": 16,
        "question": "How many tracks does each playlist have? Show the top 5 playlists.",
        "gold_sql": (
            "SELECT p.Name, COUNT(pt.TrackId) AS track_count "
            "FROM Playlist p "
            "JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId "
            "GROUP BY p.PlaylistId ORDER BY track_count DESC LIMIT 5;"
        ),
        "difficulty": "medium",
    },
    {
        "id": 17,
        "question": "Which customers from Brazil have spent more than 30 dollars in total?",
        "gold_sql": (
            "SELECT c.FirstName, c.LastName, SUM(i.Total) AS total_spent "
            "FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId "
            "WHERE c.Country = 'Brazil' "
            "GROUP BY c.CustomerId HAVING total_spent > 30 "
            "ORDER BY total_spent DESC;"
        ),
        "difficulty": "hard",
    },
    {
        "id": 18,
        "question": "What is the most expensive track in the database? Show its name and price.",
        "gold_sql": "SELECT Name, UnitPrice FROM Track ORDER BY UnitPrice DESC LIMIT 1;",
        "difficulty": "easy",
    },
    {
        "id": 19,
        "question": "How many tracks contain the word 'love' in their name?",
        "gold_sql": "SELECT COUNT(*) AS count FROM Track WHERE Name LIKE '%love%';",
        "difficulty": "medium",
    },
    {
        "id": 20,
        "question": "Which employee has handled the most customers?",
        "gold_sql": (
            "SELECT e.FirstName, e.LastName, COUNT(c.CustomerId) AS customer_count "
            "FROM Employee e JOIN Customer c ON e.EmployeeId = c.SupportRepId "
            "GROUP BY e.EmployeeId ORDER BY customer_count DESC LIMIT 1;"
        ),
        "difficulty": "medium",
    },
    {
        "id": 21,
        "question": "What is the total duration in minutes of all tracks in the 'Rock' genre?",
        "gold_sql": (
            "SELECT SUM(t.Milliseconds) / 60000.0 AS total_minutes "
            "FROM Track t JOIN Genre g ON t.GenreId = g.GenreId "
            "WHERE g.Name = 'Rock';"
        ),
        "difficulty": "medium",
    },
    {
        "id": 22,
        "question": "How many different countries have customers?",
        "gold_sql": "SELECT COUNT(DISTINCT Country) AS country_count FROM Customer;",
        "difficulty": "easy",
    },
    {
        "id": 23,
        "question": "List the 3 albums with the highest total revenue. Show the album title and revenue.",
        "gold_sql": (
            "SELECT al.Title, SUM(il.UnitPrice * il.Quantity) AS revenue "
            "FROM Album al JOIN Track t ON al.AlbumId = t.AlbumId "
            "JOIN InvoiceLine il ON t.TrackId = il.TrackId "
            "GROUP BY al.AlbumId ORDER BY revenue DESC LIMIT 3;"
        ),
        "difficulty": "hard",
    },
    {
        "id": 24,
        "question": "What is the average track length in seconds for the 'Jazz' genre?",
        "gold_sql": (
            "SELECT AVG(t.Milliseconds) / 1000.0 AS avg_seconds "
            "FROM Track t JOIN Genre g ON t.GenreId = g.GenreId "
            "WHERE g.Name = 'Jazz';"
        ),
        "difficulty": "medium",
    },
    {
        "id": 25,
        "question": "Which customers have never made a purchase?",
        "gold_sql": (
            "SELECT c.FirstName, c.LastName FROM Customer c "
            "LEFT JOIN Invoice i ON c.CustomerId = i.CustomerId "
            "WHERE i.InvoiceId IS NULL;"
        ),
        "difficulty": "hard",
    },
    {
        "id": 26,
        "question": "How many tracks are priced higher than the average track price?",
        "gold_sql": (
            "SELECT COUNT(*) AS count FROM Track "
            "WHERE UnitPrice > (SELECT AVG(UnitPrice) FROM Track);"
        ),
        "difficulty": "hard",
    },
    {
        "id": 27,
        "question": "What is the name of the artist who released the album 'Black Album'?",
        "gold_sql": (
            "SELECT ar.Name FROM Artist ar "
            "JOIN Album al ON ar.ArtistId = al.ArtistId "
            "WHERE al.Title = 'Black Album';"
        ),
        "difficulty": "medium",
    },
    {
        "id": 28,
        "question": "How many invoices have a total greater than 10 dollars?",
        "gold_sql": "SELECT COUNT(*) AS count FROM Invoice WHERE Total > 10;",
        "difficulty": "easy",
    },
    {
        "id": 29,
        "question": "List the 5 most recent invoices with the customer's full name and total.",
        "gold_sql": (
            "SELECT c.FirstName, c.LastName, i.InvoiceDate, i.Total "
            "FROM Invoice i JOIN Customer c ON i.CustomerId = c.CustomerId "
            "ORDER BY i.InvoiceDate DESC LIMIT 5;"
        ),
        "difficulty": "medium",
    },
    {
        "id": 30,
        "question": "What is the longest track in the 'Pop' genre? Show the track name and duration in seconds.",
        "gold_sql": (
            "SELECT t.Name, t.Milliseconds / 1000.0 AS duration_seconds "
            "FROM Track t JOIN Genre g ON t.GenreId = g.GenreId "
            "WHERE g.Name = 'Pop' ORDER BY t.Milliseconds DESC LIMIT 1;"
        ),
        "difficulty": "medium",
    },
]