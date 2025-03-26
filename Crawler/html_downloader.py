import requests
import re
from datetime import datetime
from url_utils import canonicalize_url
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def download_page(url):
    try:
        canonical_url = canonicalize_url(url)  # Canonicalize before request
        response = requests.get(canonical_url, timeout=10, headers={'User-Agent': 'MyCrawler/1.0'})
        accessed_time = datetime.utcnow()
        return {
            'url': canonical_url,  # Always return the canonical version
            'status_code': response.status_code,
            'html_content': response.text,
            'accessed_time': accessed_time
        }
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return {
            'url': canonical_url,  # Ensure consistency even in errors
            'status_code': None,
            'html_content': '',
            'accessed_time': datetime.utcnow()
        }
        
def download_page_with_selenium(url):
    try:
        canonical_url = canonicalize_url(url)
        accessed_time = datetime.utcnow()

        # Setup headless Chrome
        options = Options()
        options.headless = True
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(options=options)
        driver.get(canonical_url)
        driver.implicitly_wait(3)

        final_url = driver.current_url
        html = driver.page_source
        driver.quit()

        # Binary detection (based on URL or MIME guess)
        is_binary = False
        binary_extensions = ('.pdf', '.doc', '.docx', '.ppt', '.pptx')

        if final_url.lower().endswith(binary_extensions):
            is_binary = True

        # You could enhance this by checking content-type via requests.head
        # (if really needed – Selenium doesn't expose headers)

        return {
            'url': canonicalize_url(final_url),
            'status_code': 200,
            'accessed_time': accessed_time,
            'is_binary': is_binary,
            'html_content': None if is_binary else html
        }

    except Exception as e:
        print(f"[SELE] Error downloading {url} with Selenium: {e}")
        return {
            'url': canonicalize_url(url),
            'status_code': None,
            'accessed_time': datetime.utcnow(),
            'is_binary': False,
            'html_content': ''
        }

# Binary file detection del projekta

# download + binary detection funkcija
def download_page_with_binary_detection(url):
    try:
        canonical_url = canonicalize_url(url)  # Canonicalize first

        response = requests.get(canonical_url, timeout=10, headers={'User-Agent': 'MyCrawler/1.0'}, stream=True)
        accessed_time = datetime.utcnow()
        content_type = response.headers.get('Content-Type', '').lower()
        is_binary = False

        # Extension check
        binary_extensions = ('.pdf', '.doc', '.docx', '.ppt', '.pptx')
        if canonical_url.lower().endswith(binary_extensions):
            is_binary = True

        # MIME check
        if any(binary_mime in content_type for binary_mime in ['application/pdf', 'application/msword', 'application/vnd']):
            is_binary = True

        # Prepare result
        result = {
            'url': canonical_url,  # Store canonicalized URL in result
            'status_code': response.status_code,
            'accessed_time': accessed_time,
            'is_binary': is_binary,
            'html_content': None if is_binary else response.text
        }

        return result

    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return {
            'url': canonicalize_url(url),  # Ensure consistency even on error
            'status_code': None,
            'accessed_time': datetime.utcnow(),
            'is_binary': False,
            'html_content': ''
        }

def is_javascript_heavy(url):
    try:
        headers = {'User-Agent': 'MyCrawler/1.0'}
        resp = requests.get(url, timeout=5, headers=headers)
        html = resp.text.lower()

        # Če vsebuje veliko JS znakov
        script_count = html.count('<script')
        onclick_count = html.count('onclick')
        dynamic_signals = re.search(r'window\.location|document\.location|fetch\(|axios|async', html)

        if script_count >= 5 or onclick_count >= 3 or dynamic_signals:
            return True
        return False
    except Exception as e:
        print(f"[JS-DETECT] Failed to check {url}: {e}")
        return False  # fallback: assume no JS