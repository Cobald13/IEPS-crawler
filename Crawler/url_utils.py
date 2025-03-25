# URL canonization del projekta

from urllib.parse import urlparse, urlunparse

def canonicalize_url(url):
    parsed = urlparse(url)

    # Convert scheme + domain to lowercase
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Remove "www." prefix if present
    if netloc.startswith("www."):
        netloc = netloc[4:]

    # Remove fragment (#section)
    path = parsed.path
    query = parsed.query  # We keep query parameters for now

    # Remove trailing slash (except for root "/")
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    # Rebuild the URL
    canonical_url = urlunparse((scheme, netloc, path, "", query, ""))
    
    return canonical_url