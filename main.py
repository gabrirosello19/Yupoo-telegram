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

            # Conservamos los parámetros de Yupoo
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

    # Primero buscamos exactamente la siguiente página
    for numero, url in candidatos:

        if numero == pagina_actual + 1:
            return url

    # Si no aparece exactamente,
    # buscamos la página superior más cercana
    superiores = [
        (numero, url)
        for numero, url in candidatos
        if numero > pagina_actual
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
            f"{nuevos}"
        )

        print(
            f"   📊 Total acumulado: "
            f"{len(todos)}"
        )

        siguiente = encontrar_siguiente_pagina(
            soup,
            pagina
        )

        if not siguiente:

            print()
            print(
                "   ✅ No hay más páginas."
            )

            break

        print(
            f"   ➡️ Siguiente página: "
            f"{siguiente}"
        )

        url_actual = siguiente

        pagina += 1

        # Seguridad
        if pagina > 100:

            print(
                "⚠️ Límite de seguridad "
                "de 100 páginas alcanzado."
            )

            break

    print()
    print(
        f"🏁 TOTAL CATEGORÍA: "
        f"{len(todos)}"
    )

    return todos


# ============================================================
# TÍTULO
# ============================================================

def obtener_titulo(soup):

    # Open Graph
    og_title = soup.find(
        "meta",
        property="og:title"
    )

    if og_title:

        titulo = og_title.get(
            "content",
            ""
        ).strip()

        if titulo:
            return titulo

    # <title>
    if soup.title:

        titulo = soup.title.get_text(
            " ",
            strip=True
        )

        titulo = re.sub(
            r"\s*-\s*Yupoo.*$",
            "",
            titulo,
            flags=re.IGNORECASE
        )

        if titulo:
            return titulo

    # H1
    h1 = soup.find("h1")

    if h1:

        titulo = h1.get_text(
            " ",
            strip=True
        )

        if titulo:
            return titulo

    return "Producto"


# ============================================================
# ENCONTRAR IMÁGENES
# ============================================================

def encontrar_imagenes(soup):

    imagenes = []

    atributos = [
        "src",
        "data-src",
        "data-original",
        "data-lazy-src",
        "data-url",
    ]

    elementos = soup.find_all(
        ["img", "source"]
    )

    for elemento in elementos:

        for atributo in atributos:

            valor = elemento.get(
                atributo
            )

            if not valor:
                continue

            if "photo.yupoo.com" not in valor:
                continue

            imagen_url = urljoin(
                BASE_URL,
                valor
            )

            imagen_url = re.sub(
                r"/(small|thumb|thumbnail|square|big|large)/",
                "/medium/",
                imagen_url,
                flags=re.IGNORECASE
            )

            if imagen_url not in imagenes:

                imagenes.append(
                    imagen_url
                )

            break

    return imagenes


# ============================================================
# DESCARGAR IMAGEN
# ============================================================

def descargar_imagen(
    url,
    nombre
):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        ),
        "Referer": "https://x.yupoo.com/",
        "Accept": (
            "image/avif,image/webp,image/apng,"
            "image/svg+xml,image/*,*/*;q=0.8"
        ),
    }

    respuesta = session.get(
        url,
        headers=headers,
        timeout=60
    )

    print(
        f"      📥 Imagen HTTP "
        f"{respuesta.status_code}"
    )

    respuesta.raise_for_status()

    with open(
        nombre,
        "wb"
    ) as f:

        f.write(
            respuesta.content
        )

    return nombre


# ============================================================
# ENVIAR PRODUCTO A TELEGRAM
# ============================================================

def enviar_producto(
    titulo,
    archivos
):

    caption = (
        f"<b>🔥 {titulo}</b>\n\n"
        f"⚽ Urban Sport Spain\n"
        f"📩 Información y pedidos por privado."
    )

    total = len(archivos)

    print(
        f"   📸 Imágenes totales: {total}"
    )

    # --------------------------------------------------------
    # UNA FOTO
    # --------------------------------------------------------

    if total == 1:

        url = (
            f"https://api.telegram.org/"
            f"bot{TOKEN}/sendPhoto"
        )

        with open(
            archivos[0],
            "rb"
        ) as foto:

            respuesta = requests.post(
                url,
                data={
                    "chat_id": CANAL,
                    "caption": caption,
                    "parse_mode": "HTML",
                },
                files={
                    "photo": foto
                },
                timeout=60
            )

        print(
            f"   📤 Telegram HTTP "
            f"{respuesta.status_code}"
        )

        respuesta.raise_for_status()

        datos = respuesta.json()

        if not datos.get("ok"):

            raise Exception(
                f"Telegram error: {datos}"
            )

        return True

    # --------------------------------------------------------
    # VARIAS FOTOS
    # --------------------------------------------------------

    for inicio in range(
        0,
        total,
        10
    ):

        grupo = archivos[
            inicio:inicio + 10
        ]

        media = []

        archivos_abiertos = []

        try:

            for posicion, archivo in enumerate(
                grupo
            ):

                nombre_archivo = (
                    f"photo_{posicion}"
                )

                archivo_abierto = open(
                    archivo,
                    "rb"
                )

                archivos_abiertos.append(
                    (
                        nombre_archivo,
                        archivo_abierto
                    )
                )

                elemento = {
                    "type": "photo",
                    "media": (
                        f"attach://"
                        f"{nombre_archivo}"
                    ),
                }

                # Solo ponemos el texto
                # en la primera foto.
                if (
                    inicio == 0
                    and posicion == 0
                ):

                    elemento["caption"] = (
                        caption
                    )

                    elemento["parse_mode"] = (
                        "HTML"
                    )

                media.append(
                    elemento
                )

            url = (
                f"https://api.telegram.org/"
                f"bot{TOKEN}/sendMediaGroup"
            )

            files = {}

            for (
                nombre_archivo,
                archivo_abierto
            ) in archivos_abiertos:

                files[
                    nombre_archivo
                ] = archivo_abierto

            respuesta = requests.post(
                url,
                data={
                    "chat_id": CANAL,
                    "media": json.dumps(
                        media
                    ),
                },
                files=files,
                timeout=120
            )

            print(
                f"   📤 Grupo Telegram "
                f"{inicio // 10 + 1} "
                f"HTTP "
                f"{respuesta.status_code}"
            )

            respuesta.raise_for_status()

            datos = respuesta.json()

            if not datos.get("ok"):

                raise Exception(
                    f"Telegram error: {datos}"
                )

        finally:

            for (
                _,
                archivo_abierto
            ) in archivos_abiertos:

                archivo_abierto.close()

        if inicio + 10 < total:

            time.sleep(2)

    return True


# ============================================================
# PROCESAR PRODUCTO
# ============================================================

def procesar_producto(
    album_url,
    album_id
):

    print()
    print("=" * 70)

    print(
        f"🛒 PRODUCTO {album_id}"
    )

    print(
        f"🔗 {album_url}"
    )

    try:

        soup = obtener_soup(
            album_url
        )

        titulo = obtener_titulo(
            soup
        )

        print(
            f"🏷️ Título: {titulo}"
        )

        imagenes = encontrar_imagenes(
            soup
        )

        print(
            f"🖼️ Imágenes encontradas: "
            f"{len(imagenes)}"
        )

        if not imagenes:

            print(
                "❌ No se encontraron imágenes."
            )

            return False

        archivos = []

        try:

            for numero, imagen_url in enumerate(
                imagenes,
                start=1
            ):

                nombre = (
                    f"image_{numero}.jpg"
                )

                print(
                    f"   ⬇️ Descargando imagen "
                    f"{numero}"
                )

                descargar_imagen(
                    imagen_url,
                    nombre
                )

                archivos.append(
                    nombre
                )

            print(
                "📤 Enviando a Telegram..."
            )

            enviar_producto(
                titulo,
                archivos
            )

            print(
                "✅ PRODUCTO PUBLICADO"
            )

            return True

        finally:

            for archivo in archivos:

                try:

                    if os.path.exists(
                        archivo
                    ):

                        os.remove(
                            archivo
                        )

                except Exception:
                    pass

    except Exception as e:

        print(
            f"❌ ERROR PUBLICANDO "
            f"PRODUCTO: {e}"
        )

        return False


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        "🚀 YUPOO → TELEGRAM"
    )
    print("=" * 70)
    print()

    publicados = cargar_publicados()

    publicados = [
        str(x)
        for x in publicados
    ]

    print(
        f"📚 Productos ya publicados: "
        f"{len(publicados)}"
    )

    todos_los_productos = {}

    # ========================================================
    # ESCANEAR TODAS LAS CATEGORÍAS
    # Y TODAS SUS PÁGINAS
    # ========================================================

    for categoria in CATEGORIAS:

        try:

            albums = encontrar_albums_categoria(
                categoria
            )

            for album_id, album_url in albums.items():

                if album_id not in todos_los_productos:

                    todos_los_productos[
                        album_id
                    ] = {
                        "id": album_id,
                        "url": album_url,
                    }

        except Exception as e:

            print(
                f"❌ Error procesando "
                f"categoría: {e}"
            )

    # Convertir a lista
    productos = list(
        todos_los_productos.values()
    )

    print()
    print("=" * 70)

    print(
        f"📦 TOTAL PRODUCTOS ÚNICOS: "
        f"{len(productos)}"
    )

    # ========================================================
    # FILTRAR LOS YA PUBLICADOS
    # ========================================================

    nuevos = [
        producto
        for producto in productos
        if producto["id"] not in publicados
    ]

    # ========================================================
    # MÁS NUEVOS PRIMERO
    # ========================================================

    nuevos.sort(
        key=lambda x: int(x["id"]),
        reverse=True
    )

    print(
        f"🆕 PRODUCTOS NUEVOS: "
        f"{len(nuevos)}"
    )

    print(
        f"🎯 MÁXIMO POR EJECUCIÓN: "
        f"{MAX_PRODUCTS_PER_RUN}"
    )

    # ========================================================
    # SELECCIONAR LOS 5
    # ========================================================

    productos_a_publicar = nuevos[
        :MAX_PRODUCTS_PER_RUN
    ]

    if not productos_a_publicar:

        print()
        print(
            "✅ No hay productos nuevos."
        )

        return

    print()
    print(
        "📋 PRODUCTOS SELECCIONADOS:"
    )

    for producto in productos_a_publicar:

        print(
            f"   • {producto['id']} "
            f"{producto['url']}"
        )

    # ========================================================
    # PUBLICAR
    # ========================================================

    publicados_en_esta_ejecucion = 0

    for producto in productos_a_publicar:

        exito = procesar_producto(
            producto["url"],
            producto["id"]
        )

        if exito:

            publicados.append(
                producto["id"]
            )

            publicados_en_esta_ejecucion += 1

            guardar_publicados(
                publicados
            )

            print(
                f"💾 Guardado como publicado: "
                f"{producto['id']}"
            )

        else:

            print(
                f"⚠️ No se marcará como publicado: "
                f"{producto['id']}"
            )

        time.sleep(2)

    # ========================================================
    # RESUMEN FINAL
    # ========================================================

    print()
    print("=" * 70)
    print("🏁 RESUMEN FINAL")
    print("=" * 70)

    print(
        f"📦 Productos encontrados: "
        f"{len(productos)}"
    )

    print(
        f"🆕 Productos nuevos: "
        f"{len(nuevos)}"
    )

    print(
        f"📤 Publicados en esta ejecución: "
        f"{publicados_en_esta_ejecucion}"
    )

    print(
        f"💾 Total guardados como publicados: "
        f"{len(publicados)}"
    )

    print("=" * 70)


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":
    main()
