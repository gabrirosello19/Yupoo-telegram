import requests

url = "https://photo.yupoo.com/grandsuit/414a42e969/medium.jpeg"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://x.yupoo.com/",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

r = requests.get(url, headers=headers, timeout=30)

print("STATUS:", r.status_code)
print("CONTENT-TYPE:", r.headers.get("content-type"))
print("TAMAÑO:", len(r.content))
print("SERVIDOR:", r.headers.get("server"))
print("TEXTO:", r.text[:300] if "text" in r.headers.get("content-type", "") else "NO ES TEXTO")
