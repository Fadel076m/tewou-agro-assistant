from crawler import BaseCrawler
from utils.metadata import add_metadata
from utils.pdf_extractor import extract_text_from_pdf, save_extracted_text
import os
import json

class StatsScraper(BaseCrawler):
    def scrape_world_bank(self):
        urls = [
            "https://microdata.worldbank.org/index.php/catalog/6387/get-microdata",
            "https://microdata.worldbank.org/index.php/catalog/6387/data-dictionary",
            "https://microdata.worldbank.org/index.php/catalog/6386/data-dictionary/F59"
        ]
        
        for url in urls:
            self.logger.info(f"Targeting World Bank: {url}")
            # Note: Microdata catalog often requires login or JS to download
            # For now, we scrape the page content and look for PDF/CSV links
            soup = self.get_soup(url)
            if not soup:
                continue
            
            title = soup.find('h1') or soup.find('title')
            title_text = title.get_text(strip=True) if title else "World Bank Agricultural Survey"
            
            # Find PDF links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.pdf'):
                    pdf_url = urljoin(url, href)
                    self.logger.info(f"Found PDF: {pdf_url}")
                    pdf_path = self.download_file(pdf_url, os.path.join("data_collection", "raw_pdfs"))
                    if pdf_path:
                        text = extract_text_from_pdf(pdf_path)
                        save_extracted_text(text, os.path.basename(pdf_path))
                        
                        add_metadata({
                            "source_url": pdf_url,
                            "file_type": "pdf",
                            "content": f"extracted_text/{os.path.basename(pdf_path)}.txt",
                            "metadata": {
                                "title": title_text,
                                "date": "varies",
                                "language": "fr/en",
                                "category": "statistique",
                                "region": "Sénégal",
                                "file_size": f"{os.path.getsize(pdf_path)/1024:.2f} KB"
                            }
                        })
            
            # Save page content
            content = soup.get_text()
            filename = f"wb_{url.split('/')[-2]}_{url.split('/')[-1]}.json"
            output_path = os.path.join("data_collection", "web_content", filename)
            
            data = {
                "source_url": url,
                "file_type": "html",
                "content": content,
                "metadata": {
                    "title": title_text,
                    "date": "N/A",
                    "language": "en",
                    "category": "statistique",
                    "region": "Sénégal",
                    "file_size": f"{len(content)/1024:.2f} KB"
                }
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            add_metadata(data)

    def scrape_fao(self):
        url = "https://microdata.fao.org/index.php/catalog/2522/data-dictionary/F20"
        self.logger.info(f"Scraping FAO: {url}")
        soup = self.get_soup(url)
        if not soup:
            return
            
        title = "FAO Data Dictionary 2022-2023"
        content = soup.get_text()
        
        data = {
            "source_url": url,
            "file_type": "html",
            "content": content,
            "metadata": {
                "title": title,
                "date": "2022-2023",
                "language": "fr",
                "category": "statistique",
                "region": "Sénégal",
                "file_size": f"{len(content)/1024:.2f} KB"
            }
        }
        
        filename = "fao_dictionary.json"
        output_path = os.path.join("data_collection", "web_content", filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        add_metadata(data)
