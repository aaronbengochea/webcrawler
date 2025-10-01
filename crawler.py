import urllib.request
import urllib.parse
import urllib.error
import certifi
import time
import ssl
import heapq
import math
import threading
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

from config import FETCH_TIMEOUT, ROBOTS_TIMEOUT, BLACKLIST_EXT
from link_parser import LinkParser, normalize_url, get_base_domain

# Initialize SSL context 
ssl_context = ssl.create_default_context(cafile=certifi.where())

class PriorityCrawler:
    def __init__(self, seeds, max_pages, max_workers):
        self.seeds = seeds
        self.max_pages = max_pages
        self.max_workers = max_workers

        self.visited = {}            # Normalized Visited URLs -> None (Can use set as well)
        self.redirect_map = {}       # original_url -> final_normalized_url
        self.domain_counts = {}      # base_domain -> count
        self.robots_rules = {}       # Base domain -> list of disallowed paths from robots.txt
        self.heap = []               # (-priority, depth, url)
        self.log = []                # list of crawl events
        self.error_counts = {}
        self.total_bytes = 0
        self.start_time = None

        self.lock = threading.Lock()

        # Seed heap with normalized URLs
        for url in seeds:
            norm = normalize_url(url)
            pr = self.domain_priority(norm)
            heapq.heappush(self.heap, (-pr, 0, norm))

    # --- Priority based on domain usage ---
    def domain_priority(self, url):
        domain = urllib.parse.urlparse(url).netloc
        base = get_base_domain(domain)
        count = self.domain_counts.get(base, 0)
        return 1.0 / math.log(2 + count)

    # --- robots.txt fetch ---
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
        domain = p.netloc  
        rules = self.fetch_robots(domain)
        path = p.path or "/"
        for dis in rules:
            if path.startswith(dis):
                return False
        return True

    # --- Core fetch ---
    def fetch_page(self, url, depth):
        with self.lock:
            if url in self.visited or len(self.visited) >= self.max_pages:
                return

        # Skip blacklisted or CGI
        if url.lower().endswith(BLACKLIST_EXT) or "cgi" in url.lower():
            with self.lock:
                self.error_counts["pre-skip"] = self.error_counts.get("pre-skip", 0) + 1
            return
        # Skip disallowed by robots.txt
        if not self.is_allowed(url):
            with self.lock:
                self.error_counts["robots-skip"] = self.error_counts.get("robots-skip", 0) + 1
            return

        try:
            start_t = time.time()
            resp = urllib.request.urlopen(url, timeout=FETCH_TIMEOUT, context=ssl_context)

            # Track redirects
            final_url = resp.geturl()
            norm_final = normalize_url(final_url)
            if url != norm_final:
                with self.lock:
                    self.redirect_map[url] = norm_final

            with self.lock:
                if norm_final in self.visited or len(self.visited) >= self.max_pages:
                    return

            # Skip non-HTML
            ctype = resp.headers.get("Content-Type", "").lower()
            if not ctype.startswith("text/html"):
                with self.lock:
                    self.error_counts["non-html"] = self.error_counts.get("non-html", 0) + 1
                return

            # Read
            data = resp.read()
            size = len(data)
            code = resp.getcode()
            elapsed = round(time.time() - start_t, 3)

            # Log and mark visited
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
                if url != norm_final:
                    print(f"Crawled: {url} -> {norm_final} | depth={depth} | code={code} | pr={pr:.4f}")
                else:
                    print(f"Crawled: {norm_final} | depth={depth} | code={code} | pr={pr:.4f}")

            # Parse links
            parser = LinkParser(final_url)
            parser.feed(data.decode("utf-8", errors="ignore"))

            for link in parser.links:
                norm = normalize_url(link)

                # Apply redirect if any
                norm = self.redirect_map.get(norm, norm)

                # Skip Filters
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
                    # Get base domain, increment domain count, compute child priority, push to heap 
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

    # --- Crawl loop ---
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
                        if url in self.visited:
                            continue
                    futures.add(ex.submit(self.fetch_page, url, depth))

            submit_up_to_capacity()
            while futures:
                done, futures = wait(futures, return_when=FIRST_COMPLETED)
                submit_up_to_capacity()
