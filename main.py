import os
import json
import re
import time
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs


# ============================================================
# CONFIGURACIÓN
# ============================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise Exception("Falta TELEGRAM_BOT_TOKEN")

CANAL = "@urbansportspain"

BASE_URL = "https://x.yupoo.com"

MAX_PRODUCTS_PER_RUN = 5

ARCHIVO_PUBLICADOS = "published.json"


# ============================================================
# CATEGORÍAS
# ============================================================

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


# ============================================================
# SESIÓN HTTP
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
})


# ============================================================
# PUBLICADOS
# ============================================================

def cargar_publicados():

    if not os.path.exists(ARCHIVO_PUBLICADOS):
        return []

    try:

        with open(
            ARCHIVO_PUBLICADOS,
            "r",
            encoding="utf-8"
        ) as f:

            datos = json.load(f)

        if isinstance(datos, list):
            return datos

    except Exception as e:

        print(
            f"⚠️ Error leyendo published.json: {e}"
        )

    return []


def guardar_publicados(publicados):

    with open(
        ARCHIVO_PUBLICADOS,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            publicados,
            f,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# OBTENER PÁGINA
# ============================================================

def obtener_soup(url):

    print(f"🌐 Abriendo: {url}")

    respuesta = session.get(
        url,
        timeout=30
    )

    print(
        f"   HTTP {respuesta.status_code}"
    )

    respuesta.raise_for_status()

    return BeautifulSoup(
        respuesta.text,
        "html.parser"
    )


# ============================================================
# ENCONTRAR ÁLBUMES DE UNA PÁGINA
# ============================================================

def encontrar_albums(soup):

    albums = {}

    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a["href"]

        if "/albums/" not in href:
            continue

        album_url = urljoin(
            BASE_URL,
            href
        )

        match = re.search(
            r"/albums/(\d+)",
            album_url
        )

        if not match:
            continue

        album_id = match.group(1)

        if album_id not in albums:

            # IMPORTANTE:
            # Conservamos todos los parámetros
            # de la URL original de Yupoo.
            albums[album_id] = album_url

    return albums


# ============================================================
# ENCONTRAR SIGUIENTE PÁGINA
# ============================================================

def encontrar_siguiente_pagina(
    soup,
    pagina_actual
):

    candidatos = []

    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a["href"]

        if "page=" not in href:
            continue

        url = urljoin(
            BASE_URL,
            href
        )

        try:

            query = parse_qs(
                urlparse(url).query
            )

            valores = query.get("page")

            if not valores:
                continue

            numero = int(
                valores[0]
            )

            candidatos.append(
                (numero, url)
            )

        except Exception:

            continue

    # Buscamos exactamente la siguiente página
    siguiente = [
        x
        for x in candidatos
        if x[0] == pagina_actual + 1
    ]

    if siguiente:

        return siguiente[0][1]

    # Si no aparece exactamente,
    # buscamos la página superior más cercana.
    superiores = [
        x
        for x in candidatos
        if x[0] > pagina_actual
    ]

    if superiores:

        superiores.sort(
            key=lambda x: x[0]
        )

        return superiores[0][1]

    return None


# ============================================================
# ENCONTRAR TODOS LOS ÁLBUMES DE UNA CATEGORÍA
# ============================================================

def encontrar_albums_categoria(
    categoria_url
):

    todos = {}

    pagina = 1

    url_actual = categoria_url

    urls_visitadas = set()

    print()
    print("=" * 70)
    print("📂 CATEGORÍA")
    print(categoria_url)
    print("=" * 70)

    while url_actual:

        if url_actual in urls_visitadas:

            print(
                "⚠️ URL repetida. "
                "Terminando categoría."
            )

            break

        urls_visitadas.add(
            url_actual
        )

        print()
        print(
            f"📄 PÁGINA {pagina}"
        )

        try:

            soup = obtener_soup(
                url_actual
            )

        except Exception as e:

            print(
                f"❌ Error cargando página: {e}"
            )

            break

        albums = encontrar_albums(
            soup
        )

        nuevos = 0

        for album_id, album_url in albums.items():

            if album_id not in todos:

                todos[album_id] = album_url

                nuevos += 1

        print(
            f"   📦 Álbumes encontrados: "
            f"{len(albums)}"
        )

        print(
            f"   🆕 Álbumes nuevos: "
