import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser
import time
import ssl
import certifi
import heapq
import math
import threading
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

#
# Configurable Constants
#
MAX_PAGES = 15000           # Total pages to crawl
MAX_WORKERS = 30            # Number of concurrent worker threads
FETCH_TIMEOUT = 1           # Seconds for fetching HTML pages
ROBOTS_TIMEOUT = 3          # Seconds for fetching robots.txt
LOG_FILE = "crawl_log_query2_15000x30.txt"

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

#
# SSL context using certifi
#
ssl_context = ssl.create_default_context(cafile=certifi.where())

#
# HTML Link Extractor
#
class LinkParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.links = []             # Discovered links list
        self.base_url = base_url    # The current page URL for resolving relative links
        self.base_override = None   # Used to override base URL if <base> tag is found

    def handle_starttag(self, tag, attrs):
        # Override base URL if <base> is found
        if tag == 'base': 
            for (attr, value) in attrs:
                if attr == 'href':
                    self.base_override = value
        # Collect links from <a> tags
        if tag == 'a':
            for (attr, value) in attrs:
                if attr == 'href':
                    effective_base = self.base_override or self.base_url
                    self.links.append(urllib.parse.urljoin(effective_base, value))

# 
# Helpers
# 
def normalize_url(url):
    p = urllib.parse.urlparse(url)
    scheme = p.scheme.lower()
    netloc = p.netloc.lower()

    path = p.path or "/"
    for default in ("/index.html", "/index.htm", "/index.jsp", "/main.html"):
        if path.endswith(default):
            path = path[: -len(default)]
            break

    fragment = ""
    query = p.query
    return urllib.parse.urlunparse((scheme, netloc, path, "", query, fragment))

def get_base_domain(host):
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host

# 
# Crawler
# 
class PriorityCrawler:
    def __init__(self, seeds, max_pages=MAX_PAGES, max_workers=MAX_WORKERS):
        self.seeds = seeds
        self.max_pages = max_pages
        self.max_workers = max_workers

        self.visited = {}          # normalized final URLs
        self.domain_counts = {}     
        self.robots_rules = {}
        self.redirect_map = {}     # Original to final URL mappings
        self.heap = []
        self.log = []
        self.error_counts = {}
        self.total_bytes = 0
        self.start_time = None

        self.lock = threading.Lock()

        # Seed the initial starting heap
        for url in seeds:
            norm = normalize_url(url)
            pr = self.domain_priority(norm)
            heapq.heappush(self.heap, (-pr, 0, norm))

    def domain_priority(self, url):
        domain = urllib.parse.urlparse(url).netloc
        base = get_base_domain(domain)
        count = self.domain_counts.get(base, 0)
        return 1.0 / math.log(2 + count)

    def fetch_robots(self, domain):
        if domain in self.robots_rules:
            return self.robots_rules[domain]
        rules = []
        robots_url = f"https://{domain}/robots.txt"
        try:
            with urllib.request.urlopen(robots_url, timeout=ROBOTS_TIMEOUT, context=ssl_context) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
            apply = False
            for raw in content.splitlines():
                line = raw.strip()
                low = line.lower()
                if not line or low.startswith("#"):
                    continue
                if low.startswith("user-agent:"):
                    ua = line.split(":", 1)[1].strip()
                    apply = (ua == "*" or ua.lower() == "mycrawler")
                elif apply and low.startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if path:
                        rules.append(path)
        except Exception:
            pass
        self.robots_rules[domain] = rules
        return rules

    def is_allowed(self, url):
        p = urllib.parse.urlparse(url)
        base = get_base_domain(p.netloc)
        rules = self.fetch_robots(base)
        path = p.path or "/"
        for dis in rules:
            if path.startswith(dis):
                return False
        return True

    def fetch_page(self, url, depth):
        # Skip if already visited or max pages is reached
        with self.lock:
            if url in self.visited or len(self.visited) >= self.max_pages:
                return
        # Skip if URL is blacklisted
        if url.lower().endswith(BLACKLIST_EXT) or "cgi" in url.lower():
            with self.lock:
                self.error_counts["pre-skip"] = self.error_counts.get("pre-skip", 0) + 1
            return
        # Skip if disallowed by robots.txt
        if not self.is_allowed(url):
            with self.lock:
                self.error_counts["robots-skip"] = self.error_counts.get("robots-skip", 0) + 1
            return

        try:
            start_t = time.time()
            resp = urllib.request.urlopen(url, timeout=FETCH_TIMEOUT, context=ssl_context)

            # Keep track of redirects
            final_url = resp.geturl()
            norm_final = normalize_url(final_url)
            if url != norm_final:
                with self.lock:
                    self.redirect_map[url] = norm_final

            # Skip if already visited or max pages is reached
            with self.lock:
                if norm_final in self.visited or len(self.visited) >= self.max_pages:
                    return

            # Check and Skip non-HTML content
            ctype = resp.headers.get("Content-Type", "").lower()
            if not ctype.startswith("text/html"):
                with self.lock:
                    self.error_counts["non-html"] = self.error_counts.get("non-html", 0) + 1
                return

            # Read page data, gather relevant log stats
            data = resp.read()
            size = len(data)
            code = resp.getcode()
            elapsed = round(time.time() - start_t, 3)

            # Skip if already visited or max pages is reached
            # Otherwise, insert into visited map, increment total bytes, log it
            with self.lock:
                if norm_final in self.visited or len(self.visited) >= self.max_pages:
                    return
                self.visited[norm_final] = None
                self.total_bytes += size
                pr = self.domain_priority(norm_final)
                self.log.append({
                    "url": norm_final,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "size": size,
                    "depth": depth,
                    "return_code": code,
                    "priority": round(pr, 4),
                    "elapsed": elapsed
                })
                print(f"Crawled: {norm_final} | depth={depth} | code={code} | pr={pr:.4f}")

            # Gather and Parse collected links
            parser = LinkParser(final_url)  
            parser.feed(data.decode("utf-8", errors="ignore"))

            for link in parser.links:
                # Normalize links
                norm = normalize_url(link)

                # Skip if URL contains "cgi" or blacklisted
                if "cgi" in norm.lower() or norm.lower().endswith(BLACKLIST_EXT):
                    with self.lock:
                        self.error_counts["pre-skip"] = self.error_counts.get("pre-skip", 0) + 1
                    continue
                # Skip if disallowed by robots.txt
                if not self.is_allowed(norm):
                    with self.lock:
                        self.error_counts["robots-skip"] = self.error_counts.get("robots-skip", 0) + 1
                    continue
                # Break if max pages reached, Skip if already visited
                with self.lock:
                    if len(self.visited) >= self.max_pages:
                        break
                    if norm in self.visited:
                        continue
                    # get base domain, increment domain count, compute child priority, push to heap 
                    base = get_base_domain(urllib.parse.urlparse(norm).netloc)
                    self.domain_counts[base] = self.domain_counts.get(base, 0) + 1
                    pr_child = self.domain_priority(norm)
                    heapq.heappush(self.heap, (-pr_child, depth + 1, norm))

        # Handle HTTP errors separately to log status codes
        except urllib.error.HTTPError as e:
            with self.lock:
                self.error_counts[e.code] = self.error_counts.get(e.code, 0) + 1
            print(f"HTTPError: {url} (code={e.code})")
        except Exception as e:
            with self.lock:
                self.error_counts["other"] = self.error_counts.get("other", 0) + 1
            print(f"Failed: {url} ({e})")

    # Main producer-consumer crawl loop
    def crawl(self):
        self.start_time = time.time()
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = set()

            def submit_up_to_capacity():
                while len(futures) < self.max_workers:
                    with self.lock:
                        if not self.heap or len(self.visited) >= self.max_pages:
                            break
                        neg_pr, depth, url = heapq.heappop(self.heap)

                        # If this was a redirect, use its final URL
                        if url in self.redirect_map:
                            url = self.redirect_map[url]
                        # If visited then continue and do not fetch
                        if url in self.visited:
                            continue
                    # Execute fetch_page outside the lock
                    futures.add(ex.submit(self.fetch_page, url, depth))

            submit_up_to_capacity()
            while futures:
                done, futures = wait(futures, return_when=FIRST_COMPLETED)
                submit_up_to_capacity()

    def save_log(self, filename=LOG_FILE):
        total_time = round(time.time() - self.start_time, 2) if self.start_time else 0
        total_gb = self.total_bytes / (1000 ** 3)
        total_gib = self.total_bytes / (1024 ** 3)

        with open(filename, "w") as f:
            for e in self.log:
                f.write(f"{e['url']} | {e['time']} | size={e['size']} | depth={e['depth']} | "
                        f"code={e['return_code']} | priority={e['priority']} | elapsed={e['elapsed']}s\n")
            f.write("\n--- Summary Statistics ---\n")
            f.write(f"Total pages crawled: {len(self.log)}\n")
            f.write(f"Total size (bytes): {self.total_bytes}\n")
            f.write(f"Total size (GB): {total_gb:.3f}\n")
            f.write(f"Total size (GiB): {total_gib:.3f}\n")
            f.write(f"Total time (s): {total_time}\n")
            rate = round(len(self.log)/total_time, 2) if total_time > 0 else "N/A"
            f.write(f"Pages/sec: {rate}\n")
            for code, count in self.error_counts.items():
                f.write(f"Errors {code}: {count}\n")

# 
# Main Execution Loop
# 
if __name__ == "__main__":
    crawler = PriorityCrawler(SEEDS, max_pages=MAX_PAGES, max_workers=MAX_WORKERS)
    crawler.crawl()
    crawler.save_log(LOG_FILE)
