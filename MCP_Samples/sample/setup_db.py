import sqlite3

conn = sqlite3.connect("C:/QProjects/MCP_Samples/sample/users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT
)
""")

cursor.executemany("""
INSERT INTO users (name, email) VALUES (?,?)
""",[
    ("John Doe","john@example.com"),
    ("Jane Smith","jane@example.com"),
    ("Alice Johnson","alice@example.com")
])

conn.commit()
conn.close()