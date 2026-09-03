import os
import re
import requests
from bs4 import BeautifulSoup

URL = "https://x.yupoo.com/photos/grandsuit/albums/253275416?uid=1&isSubCate=false&referrercate="

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
}

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Buscar únicamente imágenes de photo.yupoo.com
found = []

for img in soup.find_all("img"):
    src = img.get("src") or img.get("data-src")

    if src and "photo.yupoo.com" in src:
        # Eliminar small/medium/square y pedir la versión grande
        src = re.sub(r"/(small|square)\.jpeg$", "/medium.jpeg", src)

        if src not in found:
            found.append(src)

print("FOTOS ENCONTRADAS:", len(found))

os.makedirs("fotos", exist_ok=True)

for i, url in enumerate(found, 1):
    print(f"Descargando {i}: {url}")

    r = requests.get(url, headers=headers, timeout=30)

    if r.status_code == 200:
        filename = f"fotos/foto_{i}.jpeg"

        with open(filename, "wb") as f:
            f.write(r.content)

        print(f"OK -> {filename} ({len(r.content)} bytes)")
    else:
        print(f"ERROR {r.status_code}: {url}")

print("PRUEBA TERMINADA")
