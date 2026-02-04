from crawler import BaseCrawler
from utils.metadata import add_metadata
import os
import json

class GeoScraper(BaseCrawler):
    def scrape_geosenegal(self):
        urls = [
            "https://www.geosenegal.gouv.sn/-geo-data-",
            "https://www.geosenegal.gouv.sn/type-de-sols.html",
            "https://www.geosenegal.gouv.sn/-base-de-donnees-geographiques-.html",
            "https://www.geosenegal.gouv.sn/-donnees-vectorielles-d-occupation-du-sol-.html"
        ]
        
        for url in urls:
            self.logger.info(f"Targeting Géo Sénégal: {url}")
            soup = self.get_soup(url)
            if not soup:
                continue
                
            title = soup.find('h1') or soup.find('title')
            title_text = title.get_text(strip=True) if title else "Géo Sénégal Data"
            
            # Look for GIS data links (GeoJSON, KML, Shapefile, etc.)
            gis_extensions = ['.geojson', '.kml', '.zip', '.csv', '.xlsx']
            content = soup.get_text()
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(href.lower().endswith(ext) for ext in gis_extensions):
                    file_url = urljoin(url, href)
                    self.logger.info(f"Found GIS/Data file: {file_url}")
                    file_path = self.download_file(file_url, os.path.join("data_collection", "structured_data"))
                    if file_path:
                        add_metadata({
                            "source_url": file_url,
                            "file_type": file_path.split('.')[-1],
                            "content": f"structured_data/{os.path.basename(file_path)}",
                            "metadata": {
                                "title": title_text,
                                "date": "N/A",
                                "language": "fr",
                                "category": "sol/sig",
                                "region": "Sénégal",
                                "file_size": f"{os.path.getsize(file_path)/1024:.2f} KB"
                            }
                        })
            
            # Save page content
            filename = f"geosenegal_{url.split('/')[-1].replace('.html', '')}.json"
            output_path = os.path.join("data_collection", "web_content", filename)
            
            data = {
                "source_url": url,
                "file_type": "html",
                "content": content,
                "metadata": {
                    "title": title_text,
                    "date": "N/A",
                    "language": "fr",
                    "category": "sol",
                    "region": "Sénégal",
                    "file_size": f"{len(content)/1024:.2f} KB"
                }
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            add_metadata(data)

    def scrape_fao_soils(self):
        url = "https://www.fao.org/4/y3948f/y3948f07.htm"
        self.logger.info(f"Scraping FAO Soils: {url}")
        soup = self.get_soup(url)
        if not soup:
            return
            
        title = "Cartographie des sols FAO - Sénégal"
        content = soup.get_text()
        
        data = {
            "source_url": url,
            "file_type": "html",
            "content": content,
            "metadata": {
                "title": title,
                "date": "N/A",
                "language": "fr",
                "category": "sol",
                "region": "Sénégal",
                "file_size": f"{len(content)/1024:.2f} KB"
            }
        }
        
        filename = "fao_soils_senegal.json"
        output_path = os.path.join("data_collection", "web_content", filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        add_metadata(data)
