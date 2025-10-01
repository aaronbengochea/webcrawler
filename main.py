# main.py
from config import SEEDS, MAX_PAGES, MAX_WORKERS, LOG_FILE
from crawler import PriorityCrawler
from logger import save_log

if __name__ == "__main__":
    crawler = PriorityCrawler(SEEDS, max_pages=MAX_PAGES, max_workers=MAX_WORKERS)
    crawler.crawl()
    save_log(LOG_FILE, crawler.log, crawler.total_bytes, crawler.start_time, crawler.error_counts)
