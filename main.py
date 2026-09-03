import requests
from bs4 import BeautifulSoup

URL = "https://x.yupoo.com/photos/grandsuit/albums/253275416?uid=1&isSubCate=false&referrercate="

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
}

response = requests.get(URL, headers=headers, timeout=30)

print("HTTP:", response.status_code)
print("URL:", response.url)
print("Tamaño:", len(response.text))

soup = BeautifulSoup(response.text, "html.parser")

images = []

for img in soup.find_all("img"):
    src = img.get("src") or img.get("data-src")
    if src and src.startswith("http"):
        images.append(src)

images = list(dict.fromkeys(images))

print("IMÁGENES ENCONTRADAS:", len(images))

for i, image in enumerate(images, 1):
    print(i, image)
