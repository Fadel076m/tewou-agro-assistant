from crawler import BaseCrawler
from utils.cleaning import clean_text, detect_language
from utils.metadata import add_metadata
import os

class NewsScraper(BaseCrawler):
    def scrape_mbeymi(self):
        url = "https://www.mbeymi.com/article/9635-chiffres-agriculture-senegal.html"
        self.logger.info(f"Scraping Mbeymi: {url}")
        soup = self.get_soup(url)
        if not soup:
            return
        
        # Extract title
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "Chiffres Agriculture Sénégal"
        
        # Extract content
        article_body = soup.find('div', class_='article-content') or soup.find('article')
        content = ""
        if article_body:
            content = clean_text(article_body.get_text())
        else:
            # Fallback
            paragraphs = soup.find_all('p')
            content = clean_text(" ".join([p.get_text() for p in paragraphs]))
            
        # Save content
        filename = "mbeymi_chiffres_agriculture.json"
        output_path = os.path.join("data_collection", "web_content", filename)
        
        data = {
            "source_url": url,
            "file_type": "html",
            "content": content,
            "metadata": {
                "title": title_text,
                "date": "N/A",
                "language": detect_language(content),
                "category": "statistique",
                "region": "Sénégal",
                "file_size": f"{len(content)/1024:.2f} KB"
            }
        }
        
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        add_metadata(data)
        self.logger.info(f"Mbeymi scrape completed and metadata added.")

    def scrape_agropasteur(self):
        url = "https://agropasteur.com/lagriculture-intelligente-face-au-climat-du-senegal-lharmonisation-des-initiatives-en-cours-lelaboration-dun-plan-dinvestissement-aic-consensuel-pour-le-sene/"
        self.logger.info(f"Scraping Agropasteur: {url}")
        soup = self.get_soup(url)
        if not soup:
            return
            
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "Agriculture Intelligente Sénégal"
        
        article_body = soup.find('div', class_='entry-content')
        content = ""
        if article_body:
            content = clean_text(article_body.get_text())
        
        data = {
            "source_url": url,
            "file_type": "html",
            "content": content,
            "metadata": {
                "title": title_text,
                "date": "N/A",
                "language": detect_language(content),
                "category": "bonne_pratique",
                "region": "Sénégal",
                "file_size": f"{len(content)/1024:.2f} KB"
            }
        }
        
        filename = "agropasteur_aic.json"
        output_path = os.path.join("data_collection", "web_content", filename)
        
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        add_metadata(data)
        self.logger.info(f"Agropasteur scrape completed.")
