import psycopg2
from urllib.parse import urlparse
from url_utils import canonicalize_url

def get_db_connection():
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
    return conn, cursor


def get_or_create_site_id(url, cursor):  # Pass cursor here
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]

    cursor.execute("SELECT id FROM site WHERE domain = %s", (domain,))
    result = cursor.fetchone()

    if result:
        return result[0]
    else:
        cursor.execute(
            "INSERT INTO site (domain) VALUES (%s) RETURNING id", (domain,)
        )
        return cursor.fetchone()[0]

def store_page_data(page_data, cursor):
    canonical_url = canonicalize_url(page_data['url'])  # Canonicalize first
    site_id = get_or_create_site_id(canonical_url, cursor)  # Use canonical URL

    cursor.execute("""
        INSERT INTO page (site_id, page_type_code, url, html_content, http_status_code, accessed_time)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        site_id,
        'HTML',
        canonical_url,  # Store only the canonicalized URL
        page_data['html_content'],
        page_data['status_code'],
        page_data['accessed_time']
    ))