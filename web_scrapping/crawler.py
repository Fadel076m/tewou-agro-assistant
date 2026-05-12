import requests
from bs4 import BeautifulSoup
import time
import os
import logging
from urllib.parse import urljoin, urlparse

class BaseCrawler:
    def __init__(self, base_url=None):
        self.base_url = base_url
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.setup_logging()

    def setup_logging(self):
        log_dir = os.path.join("data_collection", "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logging.basicConfig(
            filename=os.path.join(log_dir, "scraping.log"),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def fetch(self, url, delay=1):
        """
        Fetches the content of a URL with a delay to respect server load.
        """
        try:
            time.sleep(delay)
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Successfully fetched: {url}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    def get_soup(self, url):
        """
        Fetches a URL and returns a BeautifulSoup object.
        """
        response = self.fetch(url)
        if response:
            return BeautifulSoup(response.text, 'lxml')
        return None

    def download_file(self, url, folder, filename=None):
        """
        Downloads a file from a URL to a specific folder.
        """
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        if not filename:
            filename = os.path.basename(urlparse(url).path)
            
        # Clean filename
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        path = os.path.join(folder, filename)
        
        try:
            response = self.session.get(url, headers=self.headers, stream=True, timeout=60)
            response.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            self.logger.info(f"Downloaded file: {url} to {path}")
            return path
        except Exception as e:
            self.logger.error(f"Failed to download {url}: {e}")
            return None

import re # Added missing import
