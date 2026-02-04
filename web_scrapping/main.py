import argparse
from scrapers.news_scrapers import NewsScraper
from scrapers.weather_scrapers import WeatherScraper
from scrapers.stats_scrapers import StatsScraper
from scrapers.geo_scraper import GeoScraper
from utils.metadata import initialize_metadata
import logging

def main():
    parser = argparse.ArgumentParser(description="Tèwou Agro-Assistant Data Scraper")
    parser.add_argument("--test", action="store_true", help="Run a quick test scrape")
    args = parser.parse_args()

    # Initialize metadata file
    initialize_metadata()
    
    # Setup logging
    logging.info("Starting Tèwou Agro-Assistant Data Scraper")

    if args.test:
        print("Starting test scrape...")
        
        # Test News Scrapers
        news = NewsScraper()
        print("Scraping Mbeymi...")
        news.scrape_mbeymi()
        
        # Test Weather Scrapers
        weather = WeatherScraper()
        print("Scraping Au-Senegal...")
        weather.scrape_au_senegal()
        
        # Test Stats Scrapers (limited)
        stats = StatsScraper()
        print("Scraping FAO stats...")
        stats.scrape_fao()
        
        # Test Geo Scrapers (limited)
        geo = GeoScraper()
        print("Scraping FAO Soils...")
        geo.scrape_fao_soils()
        
        print("Test scrape completed! Check data_collection/ for results.")
    else:
        print("Running full scraping pipeline...")
        
        news = NewsScraper()
        news.scrape_mbeymi()
        news.scrape_agropasteur()
        
        weather = WeatherScraper()
        weather.scrape_au_senegal()
        weather.scrape_donnees_mondiales()
        
        stats = StatsScraper()
        stats.scrape_world_bank()
        stats.scrape_fao()
        
        geo = GeoScraper()
        geo.scrape_geosenegal()
        geo.scrape_fao_soils()
        
        print("Full scrape completed!")

if __name__ == "__main__":
    main()
