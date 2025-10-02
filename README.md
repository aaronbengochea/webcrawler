# Priority Multi Threaded Web Crawler

This project explores the design of a **multi threaded priority based web crawler** that dynamically fetches seed URLs from the **Google Custom Search API** based on a user query. From these seeds, the crawler explores web pages concurrently using a priority queue, giving preference to domains that have been crawled less. It respects `robots.txt`, avoids non-HTML resources, tracks redirects, and logs performance statistics including total pages crawled, total data size, crawl duration, and errors encountered.  

The chosen design emphasizes **performance, scalability, and extensibility**.  

---

## How to Run the Program

Follow these steps to set up and run the crawler:

### 1. Clone the Repository

```bash
git clone <your-repo-url>  
cd <your-repo-folder>  
```
---

### 2. Set Up Python Environment

Make sure you have **Python 3.8+** installed:  

```BASH  
python3 --version 
``` 

Create and activate a virtual environment (recommended):  

**macOS/Linux**  
```BASH  
python3 -m venv venv  
source venv/bin/activate
```

**Windows (PowerShell)**  
```BASH  
py -3 -m venv venv  
venv\Scripts\Activate.ps1
```  

To exit the environment later, run:  
```BASH  
deactivate  
```
---

### 3. Install Dependencies

Install required Python packages using:  

```BASH  
pip install -r requirements.txt  
```
---

### 4. Configure Environment Variables

Create a `.env` file in the project root to store your **Google API credentials**:  

```PYTHON
GOOGLE_API_KEY="your_google_api_key_here"
GOOGLE_CX="your_custom_search_engine_id_here"
```

These values are automatically loaded in `config.py` using **python-dotenv**.  

---

### 5. Update Configurations

Open **config.py** and adjust parameters if needed:  

- `SEED_QUERY` – the Google search query to generate initial seed URLs  
- `NUMBER_OF_SEEDS` – how many seed links to fetch (default: 10)  
- `MAX_PAGES` – maximum number of pages to crawl  
- `MAX_WORKERS` – number of concurrent worker threads  
- `FETCH_TIMEOUT` – timeout for fetching a page (in seconds)  
- `ROBOTS_TIMEOUT` – timeout for fetching robots.txt  
- `LOG_FILE` – output file for crawl logs  

---

### 6. Run the Crawler

Start the crawler by running:  

```BASH  
python main.py  
```
---

### 7. View Crawl Logs

After execution, results will be written to the log file specified in `config.py`  
(default: `crawl_log_DemoSample.txt`).  

The log contains:  

- Crawled URL  
- Time of crawl  
- Page size  
- Depth in crawl  
- HTTP return code  
- Priority score  
- Elapsed fetch time  

Summary statistics include:  

- Total pages crawled  
- Total data size (bytes, GB, GiB)  
- Crawl duration  
- Throughput (pages/sec)  
- Error counts  

---

## Project Structure

- **main.py** – Entry point, runs the program  
- **crawler.py** – Core crawling logic (priority queue, threading, robots, redirects)  
- **link_parser.py** – Extracts and normalizes links from HTML pages  
- **logger.py** – Handles structured logging of crawl results  
- **seed_fetcher.py** – Retrieves seed URLs via Google Custom Search API  
- **config.py** – Central configuration file (constants, environment variables)  
- **requirements.txt** – Python dependencies  
- **readme.md / readme.txt** – Documentation and setup instructions  
- **explain.txt** – High-level explanation of how the program works  

---


