import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import psycopg2

from url_utils import canonicalize_url

import hashlib

def compute_image_hash(image_data):
    return hashlib.sha256(image_data).hexdigest()

# Image extraction del projekta

def extract_and_store_images(page_id, base_url, html_content, cursor):
    base_url = canonicalize_url(base_url)
    soup = BeautifulSoup(html_content, 'html.parser')
    images = soup.find_all('img', src=True)
    count = 0

    for img_tag in images:
        img_src = img_tag['src']
        img_url = urljoin(base_url, img_src).strip()
        filename = img_url.split('/')[-1].replace('\x00', '')
        accessed_time = datetime.utcnow()

        # Oceni content_type iz končnice
        content_type = mimetypes.guess_type(img_url)[0] or 'image/unknown'

        try:
            cursor.execute("""
                INSERT INTO image (page_id, filename, content_type, data, accessed_time, image_hash)
                VALUES (%s, %s, %s, NULL, %s, NULL)
                ON CONFLICT DO NOTHING
            """, (page_id, filename, content_type, accessed_time))

            count += 1
        except Exception as e:
            print(f"Error storing image metadata for {img_url}: {e}")

    print(f"Extracted and saved {count} image metadata records from {base_url}")

