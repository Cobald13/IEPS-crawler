from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

from url_utils import canonicalize_url
from preferential_scoring import combined_score
from preferential_scoring import content_keyword_match, slovene_keywords

def extract_page_data(page_id, html_content, cursor):
    if not page_id:
        print(f"[ERROR] Invalid page_id={page_id}, skipping page_data insert.")
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    meta_keywords = ""

    # Title
    title_tag = soup.title.string if soup.title else ''
    if title_tag:
        cursor.execute("""
            INSERT INTO page_data (page_id, data_type_code, data)
            VALUES (%s, %s, %s)
        """, (page_id, 'TITLE', title_tag.strip()))

    # Description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        cursor.execute("""
            INSERT INTO page_data (page_id, data_type_code, data)
            VALUES (%s, %s, %s)
        """, (page_id, 'DESCRIPTION', meta_desc['content'].strip()))

    # Keywords
    meta_keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
    if meta_keywords_tag and meta_keywords_tag.get('content'):
        meta_keywords = meta_keywords_tag['content'].strip()
        cursor.execute("""
            INSERT INTO page_data (page_id, data_type_code, data)
            VALUES (%s, %s, %s)
        """, (page_id, 'KEYWORDS', meta_keywords))

    keyword_match_count = content_keyword_match(html_content, slovene_keywords)
    return meta_keywords, keyword_match_count

def extract_links(page_id, base_url, html_content, cursor):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a', href=True)

    for tag in links:
        href = tag['href']
        full_url = canonicalize_url(urljoin(base_url, href).split('#')[0])

        # Binary datoteke (.doc, .ppt, ...)
        if re.search(r"\.(docx?|pptx?)$", full_url, re.IGNORECASE):
            cursor.execute("""
                INSERT INTO page_data (page_id, data_type_code)
                VALUES (%s, %s)
            """, (page_id, 'BINARY_LINK'))
            continue

        # Normalno vstavi v link tabelo, če vodi na drugo stran
        cursor.execute("SELECT id FROM page WHERE url = %s", (full_url,))
        result = cursor.fetchone()
        if result:
            to_page_id = result[0]
            cursor.execute("""
                INSERT INTO link (from_page, to_page)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (page_id, to_page_id))

def extract_links_to_frontier(base_url, html_content, cursor, meta_keywords=None, keyword_match_count=0):
    base_url = canonicalize_url(base_url)  # Canonicalize base URL
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all(['a', 'div', 'span', 'button'], href=True) + soup.find_all(onclick=True)
    new_links_count = 0
    now = datetime.utcnow()  # Used for freshness scoring

    for tag in links:
        href = None

        # Standard <a href="...">
        if tag.has_attr('href'):
            href = tag['href']

        # JS onclick extraction
        elif tag.has_attr('onclick'):
            onclick_content = tag['onclick']
            match = re.search(r"(?:location\.href|document\.location)\s*=\s*[\"']([^\"']+)[\"']", onclick_content)
            if match:
                href = match.group(1)

        if href:
            full_url = urljoin(base_url, href).split('#')[0].strip()
            full_url = canonicalize_url(full_url)
            
            # Ignore only user profiles
            if "/profili" in full_url or "/delo" in full_url:
                continue


            # Compute combined priority
            priority = combined_score(tag, full_url, meta_keywords, last_accessed=now, keyword_match_count=keyword_match_count)

            try:
                cursor.execute("""
                    INSERT INTO url_frontier (url, priority)
                    VALUES (%s, %s)
                    ON CONFLICT (url) DO UPDATE SET priority = EXCLUDED.priority
                """, (full_url, float(priority)))
                new_links_count += cursor.rowcount
            except Exception as e:
                print(f"Error inserting link into frontier: {e}")

    print(f"Discovered {new_links_count} new link(s) added to frontier with smart priority.")

