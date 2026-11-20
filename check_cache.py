import sqlite3

conn = sqlite3.connect("citeverify_cache.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables in citeverify_cache.db:", c.fetchall())

for t in c.fetchall():
    t_name = t[0]
    c.execute(f"SELECT count(*) FROM {t_name}")
    print(t_name, c.fetchone()[0])
