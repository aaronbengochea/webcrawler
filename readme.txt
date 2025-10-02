Project Overview
------------------------------------------------------------
This project is a multi threaded priority based web crawler.  
It starts from a set of seed URLs which are gathered as a
function of the users query. The system then crawls pages  
concurrently while respecting robots.txt and filtering out  
undesired content types.

The crawler logs crawl results include:
- URL (normalized form)
- HTTP return code
- Page size
- Crawl depth
- Priority score
- Elapsed fetch time

------------------------------------------------------------
File List
------------------------------------------------------------

config.py
    Contains global configuration constants such as:
    - SEED_QUERY: natrual language user generated query
    - NUMBER_OF_SEEDS: number of top search engine seeds to be used
    - MAX_PAGES: total pages to crawl
    - MAX_WORKERS: number of concurrent threads
    - FETCH_TIMEOUT: number of seconds waited per http request
    - ROBOTS_TIMEOUT: number of seconds waiter per robots request
    - LOG_FILE: name of output log file
    - BLACKLIST_EXT: file extensions to skip

.env
    Used by the config.py file to load enviornment variables
    - GOOGLE_API_KEY: Google Custom Search JSON API key
    - GOOGLE_CX: Websearch engine ID (found in google project control panel)


link_parser.py
    Defines:
    - LinkParser class (extracts links from HTML <base> and <a> tags)
    - normalize_url(url): normalizes URLs
    - get_base_domain(host): collapses hostnames to base domain

crawler.py
    Defines the PriorityCrawler class:
    - Handles crawling with priority queue
    - Applies robots.txt rules
    - Manages visited set and domain counts
    - Tracks redirects in redirect_map
    - Logs crawl results

logger.py
    Utility functions to save crawl logs in readable form,  
    including statistics (total pages, total bytes, total GB/GiB,  
    errors, crawl rate, etc.)

seed_fetcher.py
    Utility for fetching seed URLs dynamically using the  
    Google Custom Search API. Given a query in config.py,  
    it retrieves the top 10 results and provides them as  
    seeds to the crawler. Requires a Google API Key and CX.

main.py
    Entry point to run the crawler.  
    Imports configuration and crawler, executes crawl, and  
    saves results to log file.

------------------------------------------------------------
How to Run
------------------------------------------------------------

1. Install Python 3 (>=3.9 recommended).

2. Install dependencies:
       pip install requirements.txt

3. Using Google Custom Search API for seeds:
   - Obtain a Google API Key
   - Obtain a Custom Search Engine (CX) ID
   - Update .env with your GOOGLE_API_KEY, GOOGLE_CX.
   - Config.py will use key and CX stored in .env
   - The crawler will fetch the top 10 results as seeds.

4. Edit config.py to adjust parameters:
   - SEED_QUERY = natrual language user generated query
   - NUMBER_OF_SEEDS: number of top search engine seeds to be used
   - MAX_PAGES = total number of pages to crawl
   - MAX_WORKERS = number of worker threads (20–50 typical)
   - FETCH_TIMEOUT, ROBOTS_TIMEOUT = timeouts in seconds
   - LOG_FILE = file where crawl results will be written

5. Run the crawler:
       python main.py

Progress will print to the console as pages are crawled.  
A detailed log will be written to user config defined LOG_FILE.

------------------------------------------------------------
Notes
------------------------------------------------------------
- The crawler respects robots.txt (basic implementation).
- Binary file types (e.g., .jpg, .pdf, .zip) are skipped.
- Redirects are tracked in redirect_map to avoid repeated crawling.
- Logs include both crawl details and summary statistics.


