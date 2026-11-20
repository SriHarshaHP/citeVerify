import sqlite3
import json

conn = sqlite3.connect("citeverify.db")
c = conn.cursor()
c.execute("SELECT claim_id, pair_id, timestamp, after_value FROM audit_log WHERE timestamp LIKE '2026-11-19T23:53%' ORDER BY claim_id")
for row in c.fetchall():
    print(row)
