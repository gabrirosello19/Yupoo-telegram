import os
import re
import requests
from bs4 import BeautifulSoup

YUPOO_URL = (
    "https://x.yupoo.com/photos/grandsuit/albums/253275416"
    "?uid=1&isSubCate=false&referrercate="
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = "@urbansportspain"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://x.yupoo.com/",
    "Accept": (
        "image/avif,image/webp,image/apng,image/svg+xml,"
        "image/*,*/*;q=0.8"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

PAGE_HEADERS = {
    "User-Agent": HEADERS["User-Agent"],
    "Referer": "https://x.yupoo.com/",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def get_album_images():
    response = requests.get(
        YUPOO_URL,
        headers=PAGE_HEADERS,
        timeout=30
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    images = []

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")

        if not src:
            continue

        if "photo.yupoo.com" not in src:
            continue

        # Nos quedamos con la versión medium, que ya hemos comprobado
        # que Yupoo permite descargar correctamente.
        src = re.sub(
            r"/(small|square)\.jpeg$",
            "/medium.jpeg",
            src
        )

        if src not in images:
            images.append(src)

    return images


def download_images(urls):
    os.makedirs("fotos", exist_ok=True)

    files = []

    for number, url in enumerate(urls, 1):
        print(f"Descargando {number}/{len(urls)}")

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        filename = f"fotos/foto_{number}.jpg"

        with open(filename, "wb") as file:
            file.write(response.content)

        print(
            f"OK: {filename} "
            f"({len(response.content)} bytes)"
        )

        files.append(filename)

    return files


def send_album(files):
    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_TOKEN}/sendMediaGroup"
    )

    media = []

    for index, filename in enumerate(files):
        item = {
            "type": "photo",
            "media": f"attach://photo{index}"
        }

        # Solo ponemos el texto en la primera foto.
        if index == 0:
            item["caption"] = (
                "🔥 NUEVO PRODUCTO\n\n"
                "📸 Catálogo Grandsuit\n\n"
                "Más información por privado."
            )

        media.append(item)

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "media": str(media).replace("'", '"')
    }

    opened_files = {}

    try:
        for index, filename in enumerate(files):
            opened_files[f"photo{index}"] = open(
                filename,
                "rb"
            )

        response = requests.post(
            url,
            data=data,
            files=opened_files,
            timeout=120
        )

        print("TELEGRAM STATUS:", response.status_code)
        print("TELEGRAM RESPONSE:", response.text)

        response.raise_for_status()

    finally:
        for file in opened_files.values():
            file.close()


def main():
    print("=== YUPOO → TELEGRAM ===")

    images = get_album_images()

    print(f"FOTOS ENCONTRADAS: {len(images)}")

    if not images:
        raise RuntimeError(
            "No se encontraron fotos en el álbum."
        )

    files = download_images(images)

    print("FOTOS DESCARGADAS:", len(files))

    send_album(files)

    print("=== PUBLICACIÓN COMPLETADA ===")


if __name__ == "__main__":
    main()
