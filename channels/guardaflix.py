# source: https://guardaflix.homes/

from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from utils import fetch, match, headers, search_parse

name = "Guardaflix"
base = "https://guardaflix.homes"

def list():
    html = fetch(base, headers=headers)
    soup = BeautifulSoup(html, "html.parser")
    out = []

    for item in soup.select(".result-item"):
        a = item.find("a")
        title_tag = item.select_one(".title")
        img_tag = item.find("img")

        if a and title_tag:
            out.append({
                "title": title_tag.text.strip(),
                "url": a["href"],
                "thumbnail": img_tag["src"] if img_tag else ""
            })

    return out

def search(query):
    html = fetch(f"{base}/?s={quote_plus(query)}", headers=headers)
    return search_parse(
        html,
        selector=".result-item",
        link_selector="a",
        title_selector=".title",
        image_selector="img"
    )

def get_links(url):
    html = fetch(url, headers=headers)
    soup = BeautifulSoup(html, "html.parser")
    out = []

    for iframe in soup.find_all("iframe"):
        src = iframe.get("src")
        if src and src.startswith("http"):
            out.append(src)

    return match(out)
