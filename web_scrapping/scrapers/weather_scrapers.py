from crawler import BaseCrawler
from utils.cleaning import clean_text, detect_language
from utils.metadata import add_metadata
import os
import json

class WeatherScraper(BaseCrawler):
    def scrape_au_senegal(self):
        url = "https://www.au-senegal.com/le-climat-et-la-meteo,046.html"
        self.logger.info(f"Scraping Au-Senegal: {url}")
        soup = self.get_soup(url)
        if not soup:
            return
            
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "Le climat et la météo au Sénégal"
        
        content_div = soup.find('div', id='content') or soup.find('article')
        content = ""
        if content_div:
            content = clean_text(content_div.get_text())
            
        data = {
            "source_url": url,
            "file_type": "html",
            "content": content,
            "metadata": {
                "title": title_text,
                "date": "N/A",
                "language": detect_language(content),
                "category": "meteo",
                "region": "Sénégal",
                "file_size": f"{len(content)/1024:.2f} KB"
            }
        }
        
        filename = "au_senegal_meteo.json"
        output_path = os.path.join("data_collection", "web_content", filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        add_metadata(data)
        self.logger.info(f"Au-Senegal weather scrape completed.")

    def scrape_donnees_mondiales(self):
        url = "https://www.donneesmondiales.com/afrique/senegal/climat.php"
        self.logger.info(f"Scraping Donnees Mondiales: {url}")
        soup = self.get_soup(url)
        if not soup:
            return
            
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "Climat du Sénégal"
        
        main_content = soup.find('main') or soup.find('div', class_='content')
        content = ""
        if main_content:
            content = clean_text(main_content.get_text())
            
        data = {
            "source_url": url,
            "file_type": "html",
            "content": content,
            "metadata": {
                "title": title_text,
                "date": "N/A",
                "language": detect_language(content),
                "category": "meteo",
                "region": "Sénégal",
                "file_size": f"{len(content)/1024:.2f} KB"
            }
        }
        
        filename = "donnees_mondiales_climat.json"
        output_path = os.path.join("data_collection", "web_content", filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        add_metadata(data)
        self.logger.info(f"Donnees Mondiales weather scrape completed.")
