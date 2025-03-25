# delay zahtevka na 5 sekund

import time
from datetime import datetime, timedelta
import socket
from urllib.parse import urlparse

last_access_times = {}  # domain_or_ip : datetime

def get_ip(domain):
    domain = domain.lower()  # Normalize domain
    if domain.startswith("www."):  # Remove "www."
        domain = domain[4:]

    try:
        return socket.gethostbyname(domain)
    except:
        return domain  # Fallback if DNS fails

def enforce_crawl_delay(url, delay_sec):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()  # Normalize domain
    if domain.startswith("www."):  # Remove "www."
        domain = domain[4:]

    ip = get_ip(domain)
    key = ip  # You can also use domain if preferred

    now = datetime.utcnow()
    last_access = last_access_times.get(key, None)

    wait_time = 0
    if last_access:
        elapsed = (now - last_access).total_seconds()
        if elapsed < delay_sec:
            wait_time = delay_sec - elapsed
            print(f"Waiting {wait_time:.2f} seconds before crawling {url}")
            time.sleep(wait_time)

    # Update last access
    last_access_times[key] = datetime.utcnow()