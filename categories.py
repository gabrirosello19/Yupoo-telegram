import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://x.yupoo.com/photos/grandsuit/categories"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://x.yupoo.com/",
}

print("LEYENDO EL CATÁLOGO...")
print("URL:", URL)

response = requests.get(
    URL,
    headers=HEADERS,
    timeout=30
)

print("HTTP:", response.status_code)
print("TAMAÑO:", len(response.text))

response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

print("\n===== ENLACES ENCONTRADOS =====\n")

encontrados = []

for a in soup.find_all("a", href=True):

    texto = a.get_text(" ", strip=True)
    href = urljoin(URL, a["href"])

    if not texto:
        continue

    # Nos interesan enlaces que puedan llevar a categorías o álbumes
    if (
        "/albums/" in href
        or "/categories/" in href
        or "/photos/" in href
    ):
        item = (texto, href)

        if item not in encontrados:
            encontrados.append(item)

for i, (texto, href) in enumerate(encontrados, 1):
    print(f"{i}. {texto}")
    print(f"   {href}")

print("\nTOTAL ENLACES:", len(encontrados))
