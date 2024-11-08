from bs4 import BeautifulSoup, Tag
import json
from enum import Enum, auto

class HandshapeBalance(Enum):
    NO_HANDSHAPES = auto()
    BOTH_PRESENT = auto()
    HANDSHAPES_ONLY = auto()

def is_handshape(char: str):
    assert len(char) == 1
    if char.isalnum() and char not in {"Z", "J"}:
        return True
    return False    

def handshapes_balance(string: str) -> HandshapeBalance:
    hs = False
    non_hs = False
    for char in string:
        if char.isspace(): continue
        if is_handshape(char): hs = True
        else: non_hs = True
    if not hs:
        return HandshapeBalance.NO_HANDSHAPES
    if not non_hs:
        return HandshapeBalance.HANDSHAPES_ONLY
    return HandshapeBalance.BOTH_PRESENT

def create_tag(soup: BeautifulSoup, name: str, attrs: dict = {}, string: str | list[str] | None = None):
    tag = soup.new_tag(name, attrs=attrs)
    if string:
        for s in string.split("<br/>"):
            tag.append(s)
            tag.append(soup.new_tag("br"))
    return tag

def main():
    with open("translations.json", encoding="utf8") as f:
        LOADED_TRANSLATIONS: dict[str, list[str]] = json.load(f)
    
    translations: dict[str, list[tuple[str, str]]] = {"Lexicon": [], "Suspiciously simplified": [], "Symbols": []}

    for meaning, transcriptions in LOADED_TRANSLATIONS.items():
        if not meaning or meaning.isspace():
            for t in transcriptions:
                translations["Symbols"].append((t, meaning))
            continue
        transcription = "<br/>".join(transcriptions)
        hs_b = handshapes_balance(transcription)
        entry = (transcription, meaning)
        if len(transcription) == 1: translations["Symbols"].append(entry)
        elif hs_b == HandshapeBalance.NO_HANDSHAPES: translations["Symbols"].append(entry)
        elif hs_b == HandshapeBalance.HANDSHAPES_ONLY: translations["Suspiciously simplified"].append(entry)
        else: translations["Lexicon"].append(entry)
    
    for l in translations.values():
        l.sort(key=lambda e: e[1].lower())

    with open("base.html", encoding="utf8") as f:
        BASE_HTML = f.read()

    soup = BeautifulSoup(BASE_HTML, "html.parser")
    insert: Tag = soup.find(attrs={"id": "sections"})
    for title, contents in translations.items():
        insert.append(create_tag(soup, "h4", {}, title))
        s_contents = create_tag(soup, "dl", {"class": "inline inline2b"})
        for asl, en in contents:
            s_contents.append(create_tag(soup, "dt", {"class": "asl"}, asl))
            s_contents.append(create_tag(soup, "dd", {}, en))
        s_content_box = create_tag(soup, "div", {"class": "medium boxshadow-p", "style": "font-family:monospace"})
        s_content_box.append(s_contents)
        insert.append(s_content_box)
    
    with open("index.html", mode="w", encoding="utf8") as f:
        f.write(soup.prettify())

if __name__ == '__main__': main()