import requests
from datetime import datetime
from url_utils import canonicalize_url

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
