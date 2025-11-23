import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

def get_domain(url):
    return urlparse(url).netloc

def crawl_seeds(seed_urls: list[str]) -> list[str]:
    found_urls = set()
    
    for url in seed_urls:
        if not url: continue
        found_urls.add(url)
        
        try:
            logger.info(f"Crawling semente: {url}")
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            base_domain = get_domain(url)

            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                
                if get_domain(full_url) == base_domain:
                    found_urls.add(full_url)
        
        except Exception as e:
            logger.warning(f"Erro ao crawlear {url}: {e}")

    return list(found_urls)