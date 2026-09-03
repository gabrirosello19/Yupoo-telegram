import os
import json
import re
import time
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


# =========================
# CONFIGURACIÓN
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise Exception("Falta TELEGRAM_BOT_TOKEN")

CANAL = "@urbansportspain"

BASE_URL = "https://x.yupoo.com"

MAX_PRODUCTS_PER_RUN = 5

CATEGORIAS = [
    "https://x.yupoo.com/photos/grandsuit/categories/5108104",
    "https://x.yupoo.com/photos/grandsuit/categories/5108105",
    "https://x.yupoo.com/photos/grandsuit/categories/5108112",
    "https://x.yupoo.com/photos/grandsuit/categories/5108233",
    "https://x.yupoo.com/photos/grandsuit/categories/18555",
    "https://x.yupoo.com/photos/grandsuit/categories/3475202",
    "https://x.yupoo.com/photos/grandsuit/categories/18559",
    "https://x.yupoo.com/photos/grandsuit/categories/3904699",
]

ARCHIVO_PUBLICADOS = "published.json"


# =========================
# SESIÓN HTTP
# =========================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
})


# =========================
# PUBLICADOS
# =========================

def cargar_publicados():
    if not os.path.exists(ARCHIVO_PUBLICADOS):
        return []

    try:
        with open(ARCHIVO_PUBLICADOS, "r", encoding="utf-8") as f:
            datos = json.load(f)

        if isinstance(datos, list):
            return datos

    except Exception as e:
        print(f"
