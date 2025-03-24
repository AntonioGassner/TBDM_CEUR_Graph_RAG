import logging
import os
import requests
from bs4 import BeautifulSoup

class Paper:
    def __init__(self, url, title, pages, author, volume_id=None):
        self.url = url
        self.title = title
        self.pages = pages
        self.author = author
        self.volume_id = volume_id

class Volume:
    def __init__(self, title, volnr, urn, pubyear, volacronym, voltitle, fulltitle, loctime, voleditor, papers=None):
        self.title = title
        self.volnr = volnr
        self.urn = urn
        self.pubyear = pubyear
        self.volacronym = volacronym
        self.voltitle = voltitle
        self.fulltitle = fulltitle
        self.loctime = loctime
        self.voleditor = voleditor

class Scraper:
    base_url = os.getenv('BASE_URL', 'https://ceur-ws.org/')

    logging.basicConfig(filename='scraping.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

    def get_all_volumes(self):
        logging.info("Getting all volumes")
        print("Getting all volumes")
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        vol_tags = soup.find_all('a', {'name': lambda value: value and value.startswith('Vol-')})
        vol_values = [tag['name'] for tag in vol_tags]
        return vol_values

    def safe_get_text(self, soup, tag, class_name):
        element = soup.find(tag, class_=class_name)
        return element.get_text() if element and element.get_text() is not None else ""

    def get_volume_metadata(self, volume_id):
        logging.info(f"Getting metadata for {volume_id}")
        print("Getting metadata for volume {}".format(volume_id))

        response = requests.get(self.base_url + volume_id)
        soup = BeautifulSoup(response.text, 'html.parser')

        volume = Volume(
            title=soup.title.get_text() if soup.title else "",
            volnr=self.safe_get_text(soup, 'span', 'CEURVOLNR'),
            urn=self.safe_get_text(soup, 'span', 'CEURURN'),
            pubyear=self.safe_get_text(soup, 'span', 'CEURPUBYEAR'),
            volacronym=self.safe_get_text(soup, 'span', 'CEURVOLACRONYM'),
            voltitle=self.safe_get_text(soup, 'span', 'CEURVOLTITLE'),
            fulltitle=self.safe_get_text(soup, 'span', 'CEURFULLTITLE'),
            loctime=self.safe_get_text(soup, 'span', 'CEURLOCTIME'),
            voleditor=[editor.get_text() for editor in soup.find_all('span', class_='CEURVOLEDITOR')]
        )
        return volume

    def safer_get_text(self, element):
        return element.get_text() if element else ""

    def get_volume_papers(self, volume_id):
        logging.info(f"Getting all papers for {volume_id}")
        print("Getting all papers for volume {}".format(volume_id))
        response = requests.get(self.base_url + volume_id)
        soup = BeautifulSoup(response.text, 'html.parser')

        papers = []
        toc_div = soup.find('div', class_='CEURTOC')
        if not toc_div:
            logging.warning(f"Volume {volume_id} does not have a TOC section")
        else:
            for li in toc_div.find_all('li'):
                title_element = li.find('span', class_='CEURTITLE')
                # Use safe_get_text to safely extract text from title_element
                title_text = self.safer_get_text(title_element)
                # Check if li has an anchor and a valid title text
                if not (li.a and title_text):
                    logging.info(f"Volume {volume_id} contains non-paper content")
                    print(f"Volume {volume_id} contains non-paper content")
                    continue

                paper = Paper(
                    url=self.base_url + volume_id + "/" + li.a.get('href'),
                    title=title_element.string,
                    pages=li.find('span', class_='CEURPAGES').string if li.find('span', class_='CEURPAGES') else None,
                    author=[author.string for author in li.find_all('span', class_='CEURAUTHOR')]
                )
                papers.append(paper)
        return papers


