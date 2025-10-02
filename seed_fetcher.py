import requests
from config import GOOGLE_API_KEY, GOOGLE_CX, SEED_QUERY, NUMBER_OF_SEEDS

def fetch_google_seeds():
    """
    Use Google Custom Search to get top NUM_SEEDS URLs for SEED_QUERY.
    Returns list of seed URLs.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": SEED_QUERY,
        "num": NUMBER_OF_SEEDS
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    j = resp.json()
    seeds = []
    for item in j.get("items", []):
        link = item.get("link")
        if link:
            seeds.append(link)
    return seeds
