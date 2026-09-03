import os
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ============================================================
# CONFIGURACIÓN
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@urbansportspain"

BASE_URL = "https://x.yupoo.com/photos/grandsuit"

MAX_PRODUCTS_PER_RUN = 5

PUBLISHED_FILE = "published.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://x.yupoo.com/",
}

IMAGE_HEADERS = {
    "User-Agent": HEADERS["User-Agent"],
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Referer": "https://x.yupoo.com/",
}

# ============================================================
# CATEGORÍAS
# ============================================================

CATEGORIES = [
    "https://x.yupoo.com/photos/grandsuit/categories/5108104",
    "https://x.yupoo.com/photos/grandsuit/categories/5108105",
    "https://x.yupoo.com/photos/grandsuit/categories/5108112",
    "https://x.yupoo.com/photos/grandsuit/categories/5108233",
    "https://x.yupoo.com/photos/grandsuit/categories/18555",
    "https://x.yupoo.com/photos/grandsuit/categories/3475202",
    "https://x.yupoo.com/photos/grandsuit/categories/18559",
    "https://x.yupoo.com/photos/grandsuit/categories/3904699",
]

# ============================================================
# FUNCIONES
# ============================================================

def limpiar(texto):
    return re.sub(r"\s+", " ", texto).strip()


def cargar_publicados():
    if not os.path.exists(PUBLISHED_FILE):
        return set()

    try:
        with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return set(str(x) for x in data)

        return set()

    except Exception:
        return set()


def guardar_publicados(publicados):
    with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
        json.dump(
            sorted(list(publicados)),
            f,
            ensure_ascii=False,
            indent=2
        )


def obtener_pagina(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    print("GET:", url)
    print("HTTP:", response.status_code)

    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")


def encontrar_albums(url):
    """
    Busca todos los enlaces /albums/ dentro de una categoría.
    También intenta seguir paginación.
    """

    albums = set()
    paginas_visitadas = set()

    pagina_url = url

    while pagina_url and pagina_url not in paginas_visitadas:

        paginas_visitadas.add(pagina_url)

        try:
            soup = obtener_pagina(pagina_url)
        except Exception as e:
            print("❌ Error leyendo categoría:", e)
            break

        # Buscar álbumes
        for a in soup.find_all("a", href=True):

            href = a["href"]

            if "/albums/" not in href:
                continue

            album_url = urljoin(BASE_URL, href)

            # Limpiar parámetros innecesarios
            album_url = album_url.split("?")[0]

            match = re.search(r"/albums/(\d+)", album_url)

            if match:
               
