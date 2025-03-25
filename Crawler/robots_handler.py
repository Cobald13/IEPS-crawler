import requests
from urllib.parse import urlparse
from urllib import robotparser

# robots.txt check

# Download and store robots.txt
def fetch_and_store_robots_txt(domain, cursor):
    domain = domain.lower()  # Normalize domain
    if domain.startswith("www."):  # Remove "www."
        domain = domain[4:]

    robots_url = f"https://{domain}/robots.txt"
    try:
        response = requests.get(robots_url, timeout=10)
        if response.status_code == 200:
            robots_content = response.text
            # Store in site.robots_content
            cursor.execute("""
                UPDATE site SET robots_content = %s WHERE domain = %s
            """, (robots_content, domain))
            print(f"robots.txt for {domain} stored.")
            return robots_content
        else:
            print(f"No robots.txt found for {domain}, status: {response.status_code}")
            return ''
    except Exception as e:
        print(f"Error fetching robots.txt for {domain}: {e}")
        return ''

# Check if crawling is allowed
def is_allowed(url, cursor):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()  # Normalize domain
    if domain.startswith("www."):  # Remove "www."
        domain = domain[4:]

    # Get robots_content from DB
    cursor.execute("SELECT robots_content FROM site WHERE domain = %s", (domain,))
    result = cursor.fetchone()
    robots_content = result[0] if result and result[0] else fetch_and_store_robots_txt(domain, cursor)

    rp = robotparser.RobotFileParser()
    rp.parse(robots_content.splitlines())
    rp.set_url(f"https://{domain}/robots.txt")

    # Set crawl delay fallback: 5 sec min
    crawl_delay = rp.crawl_delay("*")
    delay = max(crawl_delay or 0, 5)

    allowed = rp.can_fetch("*", url)
    return allowed, delay