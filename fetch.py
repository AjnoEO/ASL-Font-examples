from queue import SimpleQueue
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup, Tag
import json
from time import sleep
from random import random

BASE_URL = "https://aslfont.github.io/Symbol-Font-For-ASL/"

def unify(text: str):
    text = text.strip()
    suffixes_to_remove = ["(with orientation)", "(without)", "(abbreviation)"]
    for s in suffixes_to_remove:
        if text.endswith(s):
            text = text[:-len(s)]
            text.strip()
    if text and text[0] == '"' and (second_quote := text.find('"', 1)) > -1 and text[1].isalnum():
        text = text[1:second_quote]
    return text


def main(test: bool = False):
    if test:
        counter = 20
    else:
        counter = -1

    urls_to_check = SimpleQueue()
    urls_to_check.put(BASE_URL)
    checked_urls = set()
    translations: dict[str, set[str]] = {}

    print("> START")

    while not urls_to_check.empty() and counter != 0:
        current_url = urls_to_check.get()
        if current_url in checked_urls:
            continue
        counter -= 1
        user_agent = UserAgent().random
        response = requests.get(current_url, headers={'User-Agent': user_agent})
        if current_url == response.url:
            print(response.url, response.status_code)
        else:
            print(current_url, ">", response.url, response.status_code)
            current_url = response.url
            if current_url in checked_urls:
                print("(skipping)")
                continue
        checked_urls.add(current_url)
        current_url = current_url[:current_url.rfind('/')+1]
        if response.status_code != 200:
            continue
        soup = BeautifulSoup(response.text, 'html.parser')
        for example_block in soup.find_all('dl', {'class': 'inline'}):
            example_block: Tag
            for this_tag in example_block.find_all('dt', {'class': 'asl'}):
                this_tag: Tag
                next_tag: Tag | None = this_tag.next_sibling
                if next_tag and not next_tag.name:
                    next_tag = next_tag.next_sibling
                if next_tag and next_tag.name == 'dd':
                    asl = this_tag.get_text()
                    en = unify(next_tag.get_text())
                    if not en:
                        continue
                    translations.setdefault(en, set())
                    translations[en].add(asl)
        print(f"Translated terms: {len(translations.keys())}")
        for link in soup.find_all('a'):
            link: Tag
            url: str = link["href"]
            if '#' in url:
                continue
            if not url.startswith(('https://', 'http://')):
                url = current_url + url
            if not url.startswith(BASE_URL):
                continue
            if url in checked_urls:
                continue
            urls_to_check.put(url)
        sleep(2*random())

    with open("translations.json", mode="w", encoding="utf8") as f:
        translations = {k: list(v) for k, v in translations.items()}
        json.dump(translations, f, indent=4)

if __name__ == '__main__':
    main(test=True)