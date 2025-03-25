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
    base_url = canonicalize_url(base_url)  # Canonicalize base URL
    soup = BeautifulSoup(html_content, 'html.parser')
    images = soup.find_all('img', src=True)
    count = 0

    for img_tag in images:
        img_src = img_tag['src']
        img_url = urljoin(base_url, img_src)
        img_url = img_url.strip()

        try:
            response = requests.get(img_url, timeout=10, headers={'User-Agent': 'MyCrawler/1.0'})
            if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                content_type = response.headers.get('Content-Type')
                filename = img_url.split('/')[-1]
                filename = filename.replace('\x00', '')  # Remove null bytes just in case
                content_type = content_type.replace('\x00', '')
                data = response.content
                accessed_time = datetime.utcnow()

                image_hash = compute_image_hash(data)
                cursor.execute("SELECT id FROM image WHERE image_hash = %s", (image_hash,))
                existing_image = cursor.fetchone()

                if existing_image:
                    print(f"Duplicate image detected, skipping storage for {img_url}")
                    continue

                cursor.execute("""
                    INSERT INTO image (page_id, filename, content_type, data, accessed_time, image_hash)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (page_id, filename, content_type, psycopg2.Binary(data), accessed_time, image_hash))


                count += 1
        except Exception as e:
            print(f"Error downloading image {img_url}: {e}")

    print(f"Extracted and stored {count} image(s) from {base_url}")

