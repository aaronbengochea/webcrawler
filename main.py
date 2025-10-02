from config import MAX_PAGES, MAX_WORKERS, LOG_FILE
from seed_fetcher import fetch_google_seeds
from crawler import PriorityCrawler
from logger import save_log

if __name__ == "__main__":
    seeds = fetch_google_seeds()
    print("Seeds: " ,seeds, "\n")
    crawler = PriorityCrawler(seeds, max_pages=MAX_PAGES, max_workers=MAX_WORKERS)
    crawler.crawl()
    save_log(LOG_FILE, crawler.log, crawler.total_bytes, crawler.start_time, crawler.error_counts)
    