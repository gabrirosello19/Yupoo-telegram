import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode


BASE_URL = "https://x.yupoo.com"

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


session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
})


def obtener_soup(url):

    respuesta = session.get(
        url,
        timeout=30
    )

    print(f"      HTTP {respuesta.status_code} → {url}")

    respuesta.raise_for_status()

    return BeautifulSoup(
        respuesta.text,
        "html.parser"
    )


def encontrar_albums(soup):

    albums = {}

    for a in soup.find_all("a", href=True):

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
            albums[album_id] = album_url

    return albums


def obtener_siguiente_pagina(soup, pagina_actual):

    candidatos = []

    # Buscamos enlaces que contengan page=
    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "page=" not in href:
            continue

        texto = a.get_text(
            " ",
            strip=True
        )

        url = urljoin(
            BASE_URL,
            href
        )

        candidatos.append(
            (texto, url)
        )

    # Preferimos una página superior a la actual
    for texto, url in candidatos:

        try:

            query = parse_qs(
                urlparse(url).query
            )

            paginas = query.get("page")

            if not paginas:
                continue

            numero = int(
                paginas[0]
            )

            if numero == pagina_actual + 1:
                return url

        except Exception:
            continue

    # Si no encontramos exactamente la siguiente,
    # buscamos cualquier página superior.
    siguientes = []

    for texto, url in candidatos:

        try:

            query = parse_qs(
                urlparse(url).query
            )

            paginas = query.get("page")

            if not paginas:
                continue

            numero = int(
                paginas[0]
            )

            if numero > pagina_actual:
                siguientes.append(
                    (numero, url)
                )

        except Exception:
            continue

    if siguientes:

        siguientes.sort(
            key=lambda x: x[0]
        )

        return siguientes[0][1]

    return None


def analizar_categoria(categoria_url):

    print()
    print("=" * 70)
    print("📂 CATEGORÍA")
    print(categoria_url)
    print("=" * 70)

    todos = {}

    pagina = 1

    url_actual = categoria_url

    urls_visitadas = set()

    while url_actual:

        if url_actual in urls_visitadas:
            print("⚠️ URL repetida. Terminando categoría.")
            break

        urls_visitadas.add(url_actual)

        print()
        print(f"📄 PÁGINA {pagina}")

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
            f"   📦 Álbumes encontrados: {len(albums)}"
        )

        print(
            f"   🆕 Álbumes nuevos: {nuevos}"
        )

        print(
            f"   📊 Total acumulado: {len(todos)}"
        )

        siguiente = obtener_siguiente_pagina(
            soup,
            pagina
        )

        if not siguiente:

            print()
            print(
                "   ✅ No se ha encontrado más paginación."
            )

            break

        print(
            f"   ➡️ Siguiente página: {siguiente}"
        )

        url_actual = siguiente

        pagina += 1

        if pagina > 100:

            print(
                "⚠️ Límite de seguridad alcanzado."
            )

            break

    print()
    print(
        f"🏁 TOTAL FINAL DE ESTA CATEGORÍA: "
        f"{len(todos)}"
    )

    return todos


def main():

    total_general = {}

    print()
    print("🔎 DIAGNÓSTICO DEL CATÁLOGO YUPOO")
    print("🚫 NO SE PUBLICARÁ NADA EN TELEGRAM")
    print()

    for categoria in CATEGORIAS:

        try:

            albums = analizar_categoria(
                categoria
            )

            for album_id, album_url in albums.items():

                total_general[album_id] = album_url

        except Exception as e:

            print(
                f"❌ Error procesando categoría: {e}"
            )

    print()
    print("=" * 70)
    print("🏁 RESULTADO FINAL")
    print("=" * 70)

    print(
        f"📦 TOTAL DE PRODUCTOS ÚNICOS: "
        f"{len(total_general)}"
    )

    print()
    print(
        "🚫 No se ha enviado ningún producto a Telegram."
    )
    print(
        "🚫 published.json no se ha modificado."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
