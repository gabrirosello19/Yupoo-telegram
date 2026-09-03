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

MAX_PRODUCTS_PER_RUN = 5
PUBLISHED_FILE = "published.json"

BASE_URL = "https://x.yupoo.com/photos/grandsuit"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://x.yupoo.com/",
}

IMAGE_HEADERS = {
    "User-Agent": HEADERS["User-Agent"],
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
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
# ARCHIVO DE PRODUCTOS PUBLICADOS
# ============================================================

def cargar_publicados():
    if not os.path.exists(PUBLISHED_FILE):
        return set()

    try:
        with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return set(str(x) for x in data)

        return set()

    except Exception as e:
        print("⚠️ No se pudo leer published.json:", e)
        return set()


def guardar_publicados(publicados):
    with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
        json.dump(
            sorted(list(publicados)),
            f,
            ensure_ascii=False,
            indent=2
        )

# ============================================================
# YUPOO
# ============================================================

def obtener_soup(url):
    print()
    print("GET:", url)

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    print("HTTP:", response.status_code)

    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")


def encontrar_albums(categoria_url):
    albums = set()

    try:
        soup = obtener_soup(categoria_url)
    except Exception as e:
        print("❌ Error leyendo categoría:", e)
        return albums

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "/albums/" not in href:
            continue

        album_url = urljoin(BASE_URL, href)
        album_url = album_url.split("?")[0]

        match = re.search(r"/albums/(\d+)", album_url)

        if match:
            album_id = match.group(1)
            albums.add((album_id, album_url))

    return albums


def obtener_titulo(soup):

    og_title = soup.find(
        "meta",
        property="og:title"
    )

    if og_title and og_title.get("content"):
        titulo = og_title["content"].strip()

        if titulo:
            return titulo

    if soup.title:

        titulo = soup.title.get_text(
            " ",
            strip=True
        )

        titulo = re.sub(
            r"\s*[-|]\s*Yupoo.*$",
            "",
            titulo,
            flags=re.I
        )

        if titulo:
            return titulo

    h1 = soup.find("h1")

    if h1:
        titulo = h1.get_text(
            " ",
            strip=True
        )

        if titulo:
            return titulo

    return "Nuevo producto"


def encontrar_imagenes(soup):

    imagenes = []

    atributos = [
        "src",
        "data-src",
        "data-original",
        "data-lazy-src",
        "data-url"
    ]

    for tag in soup.find_all(
        ["img", "source"]
    ):

        for atributo in atributos:

            url = tag.get(atributo)

            if not url:
                continue

            if "photo.yupoo.com" not in url:
                continue

            url = url.replace(
                "\\/",
                "/"
            )

            url = re.sub(
                r"/(small|thumb|square|big|large)\.",
                "/medium.",
                url,
                flags=re.I
            )

            if url not in imagenes:
                imagenes.append(url)

    return imagenes

# ============================================================
# IMÁGENES
# ============================================================

def descargar_imagen(url, numero):

    try:

        response = requests.get(
            url,
            headers=IMAGE_HEADERS,
            timeout=30
        )

        print(
            "IMAGEN:",
            numero,
            "HTTP:",
            response.status_code
        )

        if response.status_code != 200:
            return None

        if not response.content:
            return None

        extension = ".jpg"

        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()

        if "png" in content_type:
            extension = ".png"

        elif "webp" in content_type:
            extension = ".webp"

        filename = f"image_{numero}{extension}"

        with open(
            filename,
            "wb"
        ) as f:
            f.write(response.content)

        return filename

    except Exception as e:

        print(
            "❌ Error descargando imagen:",
            e
        )

        return None


def borrar_archivos(archivos):

    for archivo in archivos:

        try:
            os.remove(archivo)
        except Exception:
            pass

# ============================================================
# TELEGRAM
# ============================================================

def telegram_url(method):

    return (
        "https://api.telegram.org/bot"
        + TELEGRAM_BOT_TOKEN
        + "/"
        + method
    )


def enviar_producto(titulo, archivos):

    if not archivos:
        return False

    caption = (
        f"<b>🔥 {titulo}</b>\n\n"
        f"⚽ Urban Sport Spain\n"
        f"📩 Información y pedidos por privado."
    )

    # --------------------------------------------------------
    # UNA SOLA FOTO
    # --------------------------------------------------------

    if len(archivos) == 1:

        with open(
            archivos[0],
            "rb"
        ) as foto:

            response = requests.post(
                telegram_url("sendPhoto"),
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption,
                    "parse_mode": "HTML"
                },
                files={
                    "photo": foto
                },
                timeout=60
            )

        print(
            "TELEGRAM STATUS:",
            response.status_code
        )

        print(
            "TELEGRAM RESPONSE:",
            response.text
        )

        return response.ok

    # --------------------------------------------------------
    # VARIAS FOTOS
    # --------------------------------------------------------

    grupos = [
        archivos[i:i + 10]
        for i in range(
            0,
            len(archivos),
            10
        )
    ]

    primer_grupo = True

    for grupo in grupos:

        media = []
        files = {}

        for i, archivo in enumerate(grupo):

            campo = f"photo{i}"

            media_item = {
                "type": "photo",
                "media": f"attach://{campo}"
            }

            if primer_grupo and i == 0:

                media_item["caption"] = caption
                media_item["parse_mode"] = "HTML"

            media.append(media_item)

            files[campo] = open(
                archivo,
                "rb"
            )

        try:

            response = requests.post(
                telegram_url("sendMediaGroup"),
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "media": json.dumps(media)
                },
                files=files,
                timeout=120
            )

            print(
                "TELEGRAM STATUS:",
                response.status_code
            )

            print(
                "TELEGRAM RESPONSE:",
                response.text
            )

            if not response.ok:
                return False

        finally:

            for archivo in files.values():
                archivo.close()

        primer_grupo = False

        time.sleep(2)

    return True

# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print()
    print("==========================================")
    print(" URBAN SPORT SPAIN")
    print(" YUPOO → TELEGRAM")
    print("==========================================")
    print()

    if not TELEGRAM_BOT_TOKEN:
        print("❌ FALTA TELEGRAM_BOT_TOKEN")
        return

    publicados = cargar_publicados()

    print(
        "Productos ya publicados:",
        len(publicados)
    )

    todos_albums = {}

    # --------------------------------------------------------
    # BUSCAR CATEGORÍAS
    # --------------------------------------------------------

    for categoria in CATEGORIES:

        print()
        print("==========================================")
        print("LEYENDO CATEGORÍA")
        print(categoria)
        print("==========================================")

        albums = encontrar_albums(
            categoria
        )

        print(
            "Álbumes encontrados:",
            len(albums)
        )

        for album_id, album_url in albums:

            if album_id not in todos_albums:
                todos_albums[album_id] = album_url

    print()
    print("==========================================")
    print("TOTAL PRODUCTOS ENCONTRADOS")
    print("==========================================")

    print(
        len(todos_albums)
    )

    nuevos = []

    for album_id, album_url in todos_albums.items():

        if album_id not in publicados:

            nuevos.append(
                (
                    album_id,
                    album_url
                )
            )

    print()
    print(
        "Productos nuevos:",
        len(nuevos)
    )

    print(
        "Máximo por ejecución:",
        MAX_PRODUCTS_PER_RUN
    )

    nuevos = nuevos[
        :MAX_PRODUCTS_PER_RUN
    ]

    if not nuevos:

        print()
        print(
            "✅ NO HAY PRODUCTOS NUEVOS."
        )

        return

    publicados_ahora = 0

    # --------------------------------------------------------
    # PROCESAR PRODUCTOS
    # --------------------------------------------------------

    for numero, producto in enumerate(
        nuevos,
        start=1
    ):

        album_id = producto[0]
        album_url = producto[1]

        print()
        print("==========================================")
        print(
            f"PRODUCTO {numero}/{len(nuevos)}"
        )
        print(
            "ID:",
            album_id
        )
        print(
            "URL:",
            album_url
        )
        print("==========================================")

        archivos = []

        try:

            soup = obtener_soup(
                album_url
            )

            titulo = obtener_titulo(
                soup
            )

            print(
                "TÍTULO:",
                titulo
            )

            imagenes = encontrar_imagenes(
                soup
            )

            print(
                "Imágenes encontradas:",
                len(imagenes)
            )

            if not imagenes:

                print(
                    "⚠️ No hay imágenes."
                )

                continue

            # Descargar todas las imágenes
            for i, imagen_url in enumerate(
                imagenes,
                start=1
            ):

                archivo = descargar_imagen(
                    imagen_url,
                    i
                )

                if archivo:
                    archivos.append(
                        archivo
                    )

            print(
                "Imágenes descargadas:",
                len(archivos)
            )

            if not archivos:

                print(
                    "⚠️ No se pudo descargar "
                    "ninguna imagen."
                )

                continue

            print()
            print(
                "📤 PUBLICANDO EN TELEGRAM..."
            )

            enviado = enviar_producto(
                titulo,
                archivos
            )

            if enviado:

                print(
                    "✅ PRODUCTO PUBLICADO"
                )

                publicados.add(
                    album_id
                )

                guardar_publicados(
                    publicados
                )

                publicados_ahora += 1

            else:

                print(
                    "❌ Telegram no confirmó "
                    "el envío."
                )

        except Exception as e:

            print(
                "❌ ERROR:",
                e
            )

        finally:

            borrar_archivos(
                archivos
            )

        time.sleep(3)

    print()
    print("==========================================")
    print(" RESUMEN FINAL")
    print("==========================================")
    print()
    print(
        "Publicados ahora:",
        publicados_ahora
    )
    print(
        "Total registrados:",
        len(publicados)
    )
    print()
    print("==========================================")


if __name__ == "__main__":
    main()
