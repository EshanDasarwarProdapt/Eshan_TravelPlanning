import os
import io
import zipfile
import requests

RAW_DIR = "./data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

URLS = [
    "https://archive.ics.uci.edu/static/public/485/tarvel+review+ratings.zip",
    "https://archive.ics.uci.edu/static/public/485/travel+review+ratings.zip",
    "https://archive.ics.uci.edu/static/public/485/google+review+ratings.zip"
]

def fetch_all():
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in URLS:
        try:
            print(f"Checking {url}...")
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                print(f"SUCCESS: Found archive at {url} ({len(r.content)} bytes)")
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    z.extractall(RAW_DIR)
                    print(f"Extracted files: {z.namelist()}")
            else:
                print(f"Status {r.status_code} for {url}")
        except Exception as e:
            print(f"Error checking {url}: {e}")

    print("All files in raw dir:", os.listdir(RAW_DIR))

if __name__ == "__main__":
    fetch_all()
