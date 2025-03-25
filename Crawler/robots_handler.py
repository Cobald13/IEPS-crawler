import requests
from urllib.parse import urlparse
from urllib import robotparser
import threading

robots_cache = {}  # domain -> (robots_content, parsed_parser)
cache_lock = threading.Lock()

def fetch_and_store_robots_txt(domain, cursor):
    robots_url = f"https://{domain}/robots.txt"
    try:
        response = requests.get(robots_url, timeout=10)
        if response.status_code == 200:
            robots_content = response.text
            # Store in DB
            cursor.execute("""
                UPDATE site SET robots_content = %s WHERE domain = %s
            """, (robots_content, domain))
            print(f"[ROBOTS] Stored robots.txt for {domain}")
            return robots_content
        else:
            print(f"[ROBOTS] Not found for {domain}, status: {response.status_code}")
            return ''
    except Exception as e:
        print(f"[ROBOTS] Error fetching {domain}: {e}")
        return ''

def is_allowed(url, cursor):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower().lstrip("www.")

    with cache_lock:
        if domain in robots_cache:
            rp, delay = robots_cache[domain]
        else:
            # Load from DB or fetch
            cursor.execute("SELECT robots_content FROM site WHERE domain = %s", (domain,))
            result = cursor.fetchone()
            robots_content = result[0] if result and result[0] else fetch_and_store_robots_txt(domain, cursor)

            # Parse robots.txt
            rp = robotparser.RobotFileParser()
            rp.set_url(f"https://{domain}/robots.txt")
            rp.parse(robots_content.splitlines())

            # Fallback to min 5 sec
            crawl_delay = rp.crawl_delay("*")
            delay = max(crawl_delay or 0, 5)

            # Cache
            robots_cache[domain] = (rp, delay)

    allowed = rp.can_fetch("*", url)
    return allowed, delay
