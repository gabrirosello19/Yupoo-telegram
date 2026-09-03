import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

BASE_URL = "https://x.yupoo.com/photos/grandsuit/categories"

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

# Categorías que queremos
CATEGORIAS = [
    "26/27 Club&National Men Kit (Fans Version)",
    "26/27 Club&National Men Kit (Player Version)",
    "26/27 Club&National Kids Kit",
    "26/27 Club&National Lady Kit and Belly shirt",
    "Retro Soccer jersey (S-2XL)",
    "Retro Kids soccer uniform (AAA)",
    "Adidas / Nike Soccer Jersey Set",
    "2026 Branded Tracksuit",
]


def limpiar(texto):
    return re.sub(r"\s+", " ", texto).strip().lower()


print("==========================================")
print(" BUSCADOR DE CATEGORÍAS YUPOO")
print("==========================================")
print()

print("LEYENDO:", BASE_URL)

response = requests.get(
    BASE_URL,
    headers=HEADERS,
    timeout=30
)

print("HTTP:", response.status_code)
print("TAMAÑO:", len(response.text))

response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Crear mapa nombre -> URL
categorias_encontradas = {}

for a in soup.find_all("a", href=True):
    texto = a.get_text(" ", strip=True)

    if not texto:
        continue

    href = urljoin(BASE_URL, a["href"])

    if "/categories/" not in href:
        continue

    clave = limpiar(texto)

    if clave not in categorias_encontradas:
        categorias_encontradas[clave] = (texto, href)


print()
print("==========================================")
print(" CATEGORÍAS SELECCIONADAS")
print("==========================================")
print()

seleccionadas = []

for categoria in CATEGORIAS:

    buscada = limpiar(categoria)

    encontrada = None

    # Coincidencia exacta
    if buscada in categorias_encontradas:
        encontrada = categorias_encontradas[buscada]
    else:
        # Coincidencia flexible
        for clave, valor in categorias_encontradas.items():
            if buscada in clave or clave in buscada:
                encontrada = valor
                break

    if encontrada:
        nombre, url = encontrada

        print("✅", nombre)
        print("   ", url)
        print()

        seleccionadas.append((nombre, url))

    else:
        print("❌ NO ENCONTRADA:", categoria)
        print()


print("==========================================")
print(" RESUMEN")
print("==========================================")
print()

print("Categorías solicitadas:", len(CATEGORIAS))
print("Categorías encontradas:", len(seleccionadas))

print()

if not seleccionadas:
    print("⚠️ NO SE ENCONTRÓ NINGUNA CATEGORÍA.")
else:
    print("TODO CORRECTO.")
