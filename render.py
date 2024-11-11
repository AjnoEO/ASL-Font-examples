from bs4 import BeautifulSoup, Tag
import json
from enum import Enum, auto
import re

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
    if re.match(r"^\{(\.\.?|``?)?[A-IK-Ya-z0-9](\.\.?|``?|[<>_^/Z])?\}[A-IK-Ya-z0-9]?$", string):
        # Spelling of location relative to the non-dom hand
        return HandshapeBalance.NO_HANDSHAPES
    for char in string:
        if char.isspace(): continue
        if is_handshape(char): hs = True
        else: non_hs = True
    if not hs:
        return HandshapeBalance.NO_HANDSHAPES
    if not non_hs:
        return HandshapeBalance.HANDSHAPES_ONLY
    return HandshapeBalance.BOTH_PRESENT

def create_tag(soup: BeautifulSoup, name: str, attrs: dict = {}, string: str | None = None):
    tag = soup.new_tag(name, attrs=attrs)
    if string: tag.append(BeautifulSoup(string, "html.parser"))
    return tag

def asl_dict_link(word: str):
    ASL_DICT_URL = "https://www.signasl.org/sign/"
    SUBS = {
        "'": "",
        " ": "-",
        "5": "five"
    }
    url = word
    for old, new in SUBS.items():
        url = url.replace(old, new)
    url = ASL_DICT_URL + url
    return f'<a href="{url}">{word}</a>'

def deconfixicate(string: str) -> tuple[str, str, str]:
    if string[-1] == ".": return "", string, ""
    suffix_prefixes = [", ", " on ", " ("]
    for s in suffix_prefixes:
        pos = string.find(s)
        if pos > -1:
            prefix, root, suffix = deconfixicate(string[:pos])
            return prefix, root, suffix + string[pos:]
    prefix_suffixes = [") "]
    for p in prefix_suffixes:
        pos = string.find(p)
        if pos > -1:
            pos = pos + len(p)
            prefix, root, suffix = deconfixicate(string[pos:])
            return string[:pos] + prefix, root, suffix
    return "", string, ""

def create_links(string: str):
    prefix, root, suffix = deconfixicate(string)
    if (pos := root.find("/")) > -1:
        root = asl_dict_link(root[:pos]) + "/" + asl_dict_link(root[pos+1:])
    else:
        root = asl_dict_link(root)
    return prefix + root + suffix

def fetch_tranlations() -> dict[str, list[tuple[str, str]]]:
    with open("translations.json", encoding="utf8") as f:
        LOADED_TRANSLATIONS: dict[str, list[str]] = json.load(f)
    
    TITLES_LINKS = ["Lexicon", "Suspiciously simplified"]
    TITLES_NO_LINKS = ["Phrases", "Symbols"]
    translations: dict[str, dict[str, set[str]]] = {title: {} for title in TITLES_LINKS + TITLES_NO_LINKS}
    
    for meaning, transcriptions in LOADED_TRANSLATIONS.items():
        m = deconfixicate(meaning)[1] # Extract root
        for t in transcriptions:
            hs_b = handshapes_balance(t)
            if len(t) > 1 and " " not in t and hs_b == HandshapeBalance.HANDSHAPES_ONLY:
                key = "Suspiciously simplified"
                m = m.lower()
            elif not m or m.isspace() or handshapes_balance(t) != HandshapeBalance.BOTH_PRESENT:
                key = "Symbols"
            elif (" " in t and " " in m):
                key = "Phrases"
            else:
                key = "Lexicon"
            if key in TITLES_LINKS:
                meaning = meaning.lower()
                if meaning[-1] == "?": meaning
            translations[key].setdefault(meaning, set())
            translations[key][meaning].add(t)

    return {
        title: [("<br/>".join(t), create_links(m) if title in TITLES_LINKS else m) for m, t in translations[title].items()]
        for title in translations
    }

def main():
    translations = fetch_tranlations()
    
    for l in translations.values():
        l.sort(key=lambda e: deconfixicate(e[1])[1].lower())

    with open("base.html", encoding="utf8") as f:
        BASE_HTML = f.read()

    soup = BeautifulSoup(BASE_HTML, "html.parser")
    insert: Tag = soup.find(attrs={"id": "sections"})
    for title, contents in translations.items():
        insert.append(create_tag(soup, "h4", {}, title))
        s_contents = create_tag(soup, "dl", {"class": "inline inline2d" if title != "Phrases" else "inline inline1c"})
        for asl, en in contents:
            s_contents.append(create_tag(soup, "dt", {"class": "asl"}, asl))
            s_contents.append(create_tag(soup, "dd", {}, en))
        s_content_box = create_tag(soup, "div", {"class": "medium boxshadow-p", "style": "font-family:monospace"})
        s_content_box.append(s_contents)
        insert.append(s_content_box)
    
    with open("index.html", mode="w", encoding="utf8") as f:
        f.write(str(soup))

if __name__ == '__main__': main()