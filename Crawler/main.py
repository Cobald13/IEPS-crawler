from crawler_core import start_crawler
from seed_urls import seed_urls  # Optional: run seed logic automatically

if __name__ == "__main__":
    # Optionally seed URLs here, or call seed_urls() if modularized
    print("[INFO] Starting multi-threaded crawler with 5 workers...")
    start_crawler(num_workers=5)
