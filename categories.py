import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://grandsuit.x.yupoo.com/albums/?lang=en-US"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

print("LEYENDO EL CATÁLOGO...")

response = requests.get(
    URL,
    headers=HEADERS,
    timeout=30
)

print("HTTP:", response.status_code)

response.raise_for_status()

soup = BeautifulSoup(
    response.text,
    "html.parser"
)

print("\n===== ENLACES ENCONTRADOS =====\n")

links = []

for link in soup.find_all("a", href=True):

    name = link.get_text(
        " ",
        strip=True
    )

    href = urljoin(
        URL,
        link["href"]
    )

    if name and "category" in href.lower():

        item = (name, href)

        if item not in links:
            links.append(item)

for number, (name, href) in enumerate(
    links,
    1
):
    print(f"{number}. {name}")
    print(f"   {href}")

print(
    "\nTOTAL CATEGORÍAS:",
    len(links)
)
