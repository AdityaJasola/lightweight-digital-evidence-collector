import sqlite3

conn = sqlite3.connect("instance/evidence.db")

result = conn.execute(
    "SELECT stored_filename FROM evidence WHERE evidence_code = ?",
    ("EV-20261103-DC6F30",)
).fetchone()

print("Stored filename:", result)

conn.close()
