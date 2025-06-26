from utils import fetch, match, headers
from bs4 import BeautifulSoup

def get_video_links(url):
    html = fetch(url, headers=headers)
    soup = BeautifulSoup(html, "html.parser")

    iframe_links = []
    for iframe in soup.select("iframe"):
        src = iframe.get("src")
        if src and src.startswith("http"):
            iframe_links.append(src)

    # Usa match() per risolvere link da Mega, Dood, Voe, ecc.
    return match(iframe_links)
