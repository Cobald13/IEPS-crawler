# thread pool setup
def get_next_urls_to_crawl(cursor, limit=10):
    cursor.execute("""
        SELECT url FROM url_frontier
        WHERE status = 'queued'
        ORDER BY priority ASC
        LIMIT %s
    """, (limit,))
    return [row[0] for row in cursor.fetchall()]

# to smo dali vn pri sortiranju -> , discovered_at ASC