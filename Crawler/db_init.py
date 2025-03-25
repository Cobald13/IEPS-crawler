import psycopg2

# Database connection parameters
conn = psycopg2.connect(
    dbname='wier',
    user='user',
    password='SecretPassword',
    host='localhost',
    port='5433'
)
conn.autocommit = True
cursor = conn.cursor()

# Ensure correct schema
cursor.execute("SET search_path TO crawldb;")

# Insert required page_type codes
page_types = ['HTML', 'BINARY', 'DUPLICATE', 'FRONTIER']
for pt in page_types:
    cursor.execute("""
        INSERT INTO page_type (code) VALUES (%s)
        ON CONFLICT DO NOTHING;
    """, (pt,))
print(f"[INIT] Inserted {len(page_types)} page_type codes.")

# Insert required data_type codes
data_types = ['TITLE', 'DESCRIPTION', 'KEYWORDS', 'FILENAME']
for dt in data_types:
    cursor.execute("""
        INSERT INTO data_type (code) VALUES (%s)
        ON CONFLICT DO NOTHING;
    """, (dt,))
print(f"[INIT] Inserted {len(data_types)} data_type codes.")

cursor.close()
conn.close()
print("[INIT] Database initialization complete.")
