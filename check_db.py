import sqlite3

conn = sqlite3.connect("citeverify.db")
c = conn.cursor()
c.execute("SELECT claim_id, pair_id, before_value, after_value, note FROM audit_log ORDER BY timestamp DESC LIMIT 35")
for r in c.fetchall():
    print(r)
