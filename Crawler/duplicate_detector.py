#duplication check s hashiranjem
import hashlib

from url_utils import canonicalize_url
from db_interface import get_or_create_site_id

def compute_content_hash(html_content):
    return hashlib.sha256(html_content.encode('utf-8')).hexdigest()

def store_page_with_duplicate_detection(result, cursor, from_page_id=None):
    url = canonicalize_url(result['url'])  # Canonicalize URL
    site_id = get_or_create_site_id(url, cursor)

    # Handle Binary Files First
    if result.get('is_binary', False):
        try:
            cursor.execute("""
                INSERT INTO page (site_id, page_type_code, url, http_status_code, accessed_time)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                site_id, 'BINARY', url, result['status_code'], result['accessed_time']
            ))
            page_id = cursor.fetchone()[0]

            # Verify page_id exists
            cursor.execute("SELECT id FROM page WHERE id = %s", (page_id,))
            if not cursor.fetchone():
                print(f"[ERROR] Inserted BINARY page_id={page_id} not found, skipping page_data.")
                return None

            print(f"Stored BINARY page_id={page_id} for {url}")

            # Safe filename insert
            filename = url.split('/')[-1].replace('\x00', '')
            cursor.execute("""
                INSERT INTO page_data (page_id, data_type_code, data)
                VALUES (%s, %s, %s)
            """, (page_id, 'FILENAME', filename))

            return page_id

        except Exception as e:
            print(f"[ERROR] Binary page insert failed for {url}: {e}")
            return None

    # Handle HTML
    html_content = result['html_content']
    if html_content is None:
        print(f"[WARN] HTML content is None for {url}, skipping.")
        return None

    content_hash = compute_content_hash(html_content)

    try:
        # Check if URL already exists
        cursor.execute("SELECT id, content_hash FROM page WHERE url = %s", (url,))
        existing_page = cursor.fetchone()

        if existing_page:
            page_id = existing_page[0]
            cursor.execute("""
                UPDATE page
                SET html_content = %s, http_status_code = %s, accessed_time = %s, content_hash = %s
                WHERE id = %s
            """, (html_content, result['status_code'], result['accessed_time'], content_hash, page_id))
            print(f"Updated page_id={page_id} content.")

        else:
            # Check for duplicate content (hash)
            cursor.execute("SELECT id FROM page WHERE content_hash = %s", (content_hash,))
            duplicate_page = cursor.fetchone()

            if duplicate_page:
                cursor.execute("""
                    INSERT INTO page (site_id, page_type_code, url, http_status_code, accessed_time, content_hash)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (site_id, 'DUPLICATE', url, result['status_code'], result['accessed_time'], content_hash))
                page_id = cursor.fetchone()[0]
                print(f"Stored DUPLICATE page_id={page_id} of {duplicate_page[0]}")
            else:
                cursor.execute("""
                    INSERT INTO page (site_id, page_type_code, url, html_content, http_status_code, accessed_time, content_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (site_id, 'HTML', url, html_content, result['status_code'], result['accessed_time'], content_hash))
                page_id = cursor.fetchone()[0]
                print(f"Stored page_id={page_id} as new HTML page.")

        # Verify page_id exists post-insert/update
        cursor.execute("SELECT id FROM page WHERE id = %s", (page_id,))
        if not cursor.fetchone():
            print(f"[ERROR] page_id={page_id} not found after insert/update. Skipping link.")
            return None

        # Insert link (safe)
        if from_page_id:
            # Resolve from_page_id from URL to page ID
            canonical_from_url = canonicalize_url(from_page_id)
            cursor.execute("SELECT id FROM page WHERE url = %s", (canonical_from_url,))
            from_result = cursor.fetchone()
        
            if from_result:
                from_page_real_id = from_result[0]
                cursor.execute("""
                    INSERT INTO link (from_page, to_page)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                """, (from_page_real_id, page_id))


        return page_id

    except Exception as e:
        print(f"[ERROR] HTML page insert failed for {url}: {e}")
        return None
