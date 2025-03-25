import psycopg2
from url_utils import canonicalize_url

# Database connection
conn = psycopg2.connect(
    dbname='wier',
    user='user',
    password='SecretPassword',
    host='localhost',
    port='5433'
)
conn.autocommit = True
cursor = conn.cursor()
cursor.execute("SET search_path TO crawldb;")

# Seed URLs
seed_urls = [
    "https://slo-tech.com/",
    "https://slo-tech.com/forum/isci/?q=chat+gpt",
    "https://slo-tech.com/forum/isci/?q=chatgpt",
    "https://slo-tech.com/clanki/"
]

# Insert into frontier
for seed_url in seed_urls:
    cursor.execute("""
        INSERT INTO url_frontier (url, priority)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING;
    """, (canonicalize_url(seed_url), 0))

print(f"Seeded {len(seed_urls)} URL(s) into url_frontier.")

cursor.close()
conn.close()