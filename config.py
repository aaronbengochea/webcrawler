# Configuration for the web crawler

MAX_PAGES = 1000           # Total pages to crawl
MAX_WORKERS = 50            # Number of concurrent worker threads
FETCH_TIMEOUT = 1           # Seconds for fetching HTML pages
ROBOTS_TIMEOUT = 3          # Seconds for fetching robots.txt
LOG_FILE = "crawl_log_query2_test_15000x30.txt"

SEEDS = [
    "https://www.ustires.org/tires-101/how-tire-made",
    "https://www.michelinman.com/auto/auto-tips-and-advice/tires-101/how-are-tires-made",
    "https://www.maxxis.com/us/technology/how-a-tire-is-made/",
    "https://www.gotodobbs.com/blog/tires-construction-size/",
    "https://www.goodyear.com/en_US/learn/tire-basics/how-are-tires-made.html",
    "https://www.ace-laboratories.com/how-are-tires-made/",
    "https://na.nokiantyres.com/tips/choosing-your-tires/how-are-tires-made/",
    "https://www.elitetireandautoservice.net/About/News/ArticleID/17888",
    "https://www.valoroffroad.com/blogs/the-source/how-is-a-tire-made?srsltid=AfmBOoqYUlvwa_7RzeCDxxBzEZvg2d4Bm8EgOEg5mhn-Ae3KElarbiLC",
    "https://www.nexentire.com/international/information/tire_information/basic_sense/process.php",
]

BLACKLIST_EXT = (
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", 
    ".pptx", ".mp3", ".wav", ".mp4", ".avi", ".mov",
    ".zip", ".rar", ".gz", ".tar"
)