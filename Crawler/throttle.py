# delay zahtevka na 5 sekund

import time
from datetime import datetime
import socket
from urllib.parse import urlparse
import threading

last_access_times = {}  # key = IP (or domain)
lock = threading.Lock()  # thread-safe lock for access control

def get_ip(domain):
    domain = domain.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    try:
        return socket.gethostbyname(domain)
    except:
        return domain  # fallback

def enforce_crawl_delay(url, delay_sec):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]

    ip = get_ip(domain)
    key = ip  # or domain if IP not preferred

    now = datetime.utcnow()

    with lock:
        last_access = last_access_times.get(key, None)

        wait_time = 0
        if last_access:
            elapsed = (now - last_access).total_seconds()
            if elapsed < delay_sec:
                wait_time = delay_sec - elapsed
                print(f"[THROTTLE] Waiting {wait_time:.2f}s before crawling {url}")
                time.sleep(wait_time)

        # update access time after (even if wait_time was 0)
        last_access_times[key] = datetime.utcnow()