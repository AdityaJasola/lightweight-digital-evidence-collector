import sqlite3

conn = sqlite3.connect("instance/evidence.db")

tables = conn.execute("""
SELECT name, sql
FROM sqlite_master
WHERE type = 'table'
""").fetchall()

for name, sql in tables:
    print("\nTABLE:", name)
    print(sql)

conn.close()