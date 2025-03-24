import logging
from concurrent.futures import ThreadPoolExecutor
from scraper.scraper import Scraper
from db.database import Database
from dotenv import load_dotenv

logging.basicConfig(filename='scraping.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_volume(volume_id, scraper, database):
    if database.volume_exists(volume_id):
        logging.info(f"Volume {volume_id} already in database")
        return
            
    # Get and save volume to database
    volume_metadata = scraper.get_volume_metadata(volume_id)
    volume_object_id = database.save_volume(volume_metadata.__dict__)

    # Get and save papers to database
    volume_papers = scraper.get_volume_papers(volume_id)
    for paper in volume_papers:
        paper.volume_id = volume_object_id
        database.save_paper(paper.__dict__)

def main():
    load_dotenv(dotenv_path="web-scraper/.env")

    scraper = Scraper()
    database = Database()

    all_volumes = scraper.get_all_volumes()

    with ThreadPoolExecutor(max_workers=20) as executor:  # Adjust max_workers as needed
        # Submit each volume scraping task to executor
        futures = []
        for volume_id in all_volumes:
            futures.append(executor.submit(scrape_volume, volume_id, scraper, database))

        # Wait for all tasks to complete
        for future in futures:
            future.result() 

if __name__ == "__main__":
    main()