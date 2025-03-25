# Multi-worker crawler del projekta

from url_utils import canonicalize_url
from robots_handler import is_allowed
from throttle import enforce_crawl_delay
from html_downloader import download_page_with_binary_detection
from duplicate_detector import store_page_with_duplicate_detection
from data_extractor import extract_page_data, extract_links_to_frontier
from image_extractor import extract_and_store_images

from concurrent.futures import ThreadPoolExecutor
import psycopg2
from url_frontier import get_next_urls_to_crawl

# crawl funkcija za en URL
def crawl_one_url(url):
    try:
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

        url = canonicalize_url(url)

        # Check already crawled
        cursor.execute("SELECT id FROM page WHERE url = %s", (url,))
        if cursor.fetchone():
            print(f"[SKIP] Already crawled: {url}")
            cursor.execute("UPDATE url_frontier SET status = %s WHERE url = %s", ('crawled', url))
            cursor.close()
            conn.close()
            return

        allowed, delay = is_allowed(url, cursor)
        if not allowed:
            print(f"[SKIP] Disallowed by robots.txt: {url}")
            cursor.execute("UPDATE url_frontier SET status = %s WHERE url = %s", ('failed', url))
            cursor.close()
            conn.close()
            return

        enforce_crawl_delay(url, delay)
        result = download_page_with_binary_detection(url)

        if not result or not result.get('url'):
            print(f"[ERROR] Download failed for {url}")
            cursor.execute("UPDATE url_frontier SET status = %s WHERE url = %s", ('failed', url))
            cursor.close()
            conn.close()
            return

        page_id = store_page_with_duplicate_detection(result, cursor)
        if not page_id:
            print(f"[ERROR] Page store failed for {url}")
            cursor.execute("UPDATE url_frontier SET status = %s WHERE url = %s", ('failed', url))
            cursor.close()
            conn.close()
            return

        if not result.get('is_binary', False):
            meta_keywords = extract_page_data(page_id, result['html_content'], cursor)
            extract_links_to_frontier(result['url'], result['html_content'], cursor, meta_keywords)
            extract_and_store_images(page_id, result['url'], result['html_content'], cursor)

        cursor.execute("UPDATE url_frontier SET status = %s WHERE url = %s", ('crawled', url))
        print(f"[CRAWLED] {url}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR] Failed to crawl {url}: {e}")
        try:
            cursor.execute("UPDATE url_frontier SET status = %s WHERE url = %s", ('failed', url))
            cursor.close()
            conn.close()
        except:
            pass  # if cursor/conn fails

# main loop with workers
def start_crawler(num_workers):
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

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        while True:
            urls = get_next_urls_to_crawl(cursor, limit=num_workers)
            if not urls:
                print("No URLs left to crawl. Frontier empty.")
                break

            # Submit crawl jobs
            futures = [executor.submit(crawl_one_url, url) for url in urls]

            # Wait for all to complete
            for future in futures:
                future.result()  # Raises exceptions if any

    cursor.close()
    conn.close()
