import sqlite3

conn = sqlite3.connect("instance/evidence.db")

rows = conn.execute("""
SELECT evidence_code, evidence_name, stored_filename, sha256_hash
FROM evidence
""").fetchall()

for row in rows:
    print("\nEvidence ID:", row[0])
    print("Evidence Name:", row[1])
    print("Stored Filename:", row[2])
    print("SHA-256:", row[3])

conn.close()
