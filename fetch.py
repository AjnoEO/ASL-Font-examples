from queue import SimpleQueue
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup, Tag
import json
from time import sleep
from random import random

BASE_URL = "https://aslfont.github.io/Symbol-Font-For-ASL/"

def main(test: bool = False):
    if test:
        counter = 20
    else:
        counter = -1

    urls_to_check = SimpleQueue()
    urls_to_check.put(BASE_URL)
    checked_urls = {BASE_URL}
    translations: dict[str, set[str]] = {}

    print("> START")

    while not urls_to_check.empty() and counter != 0:
        counter -= 1
        user_agent = UserAgent().random
        current_url = urls_to_check.get()
        response = requests.get(current_url, headers={'User-Agent': user_agent})
        if current_url == response.url:
            print(response.url, response.status_code)
        else:
            print(current_url, ">", response.url, response.status_code)
            current_url = response.url
        current_url = current_url[:current_url.rfind('/')+1]
        if response.status_code != 200:
            continue
        soup = BeautifulSoup(response.text, 'html.parser')
        for example_block in soup.find_all('dl', {'class': 'inline'}):
            example_block: Tag
            last_asl = last_en = None
            for tag in example_block.children:
                tag: Tag
                if tag.name == 'dt' and 'class' in tag.attrs and 'asl' in tag.attrs['class']:
                    last_asl = tag.get_text()
                    continue
                elif tag.name == 'dd' and last_asl:
                    last_en = tag.get_text()
                    translations.setdefault(last_en, set())
                    translations[last_en].add(last_asl)
                last_asl = last_en = None
        print(f"Translated terms: {len(translations.keys())}")
        for link in soup.find_all('a'):
            link: Tag
            url: str = link["href"]
            # print(">", link.get_text(), url)
            if '#' in url:
                continue
            if not url.startswith(('https://', 'http://')):
                url = current_url + url
            if not url.startswith(BASE_URL):
                continue
            if url in checked_urls:
                continue
            urls_to_check.put(url)
            checked_urls.add(url)
        sleep(1+2*random())

    with open("translations.json", mode="w", encoding="utf8") as f:
        translations = {k: list(v) for k, v in translations.items()}
        json.dump(translations, f, indent=4)

if __name__ == '__main__':
    main(test=True)