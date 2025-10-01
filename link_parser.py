import urllib.parse
from html.parser import HTMLParser

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