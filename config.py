import os
from dotenv import load_dotenv
load_dotenv()

SEED_QUERY = "how are tires made"
NUMBER_OF_SEEDS = 10                    # Number of seed URLs to fetch via Google Custom Search API
MAX_PAGES = 50                         # Total pages to crawl
MAX_WORKERS = 50                        # Number of concurrent worker threads
FETCH_TIMEOUT = 1                       # Seconds for fetching HTML pages
ROBOTS_TIMEOUT = 3                      # Seconds for fetching robots.txt
LOG_FILE = "crawl_log_DemoSample.txt"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

BLACKLIST_EXT = (
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", 
    ".pptx", ".mp3", ".wav", ".mp4", ".avi", ".mov",
    ".zip", ".rar", ".gz", ".tar"
)