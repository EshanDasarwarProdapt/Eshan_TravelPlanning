import os
import io
import zipfile
import requests
import pandas as pd
from urllib.parse import urlparse

RAW_DIR = "./data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

# UCI Dataset 485 URL and Travel Review Ratings Mirrors
UCI_485_ZIP_URL = "https://archive.ics.uci.edu/static/public/485/restaurant+consumer+data.zip"
TRIPADVISOR_DATASET_URL = "https://archive.ics.uci.edu/static/public/484/travel+reviews.zip"

def download_uci_dataset():
    """
    Downloads and extracts dataset directly from the UCI Machine Learning Repository
    for Dataset 485 (Travel & Consumer Ratings) and related travel review records.
    """
    print(f"[*] Fetching UCI Dataset 485 from official repository...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    downloaded = False
    
    # 1. Try UCI 485
    try:
        resp = requests.get(UCI_485_ZIP_URL, headers=headers, timeout=15)
        if resp.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                z.extractall(RAW_DIR)
            print(f"[✔] Successfully downloaded and extracted UCI 485 archive to {RAW_DIR}")
            downloaded = True
    except Exception as e:
        print(f"[!] Note on UCI 485 direct download: {e}")

    # 2. Also try Travel Reviews if available
    try:
        resp2 = requests.get(TRIPADVISOR_DATASET_URL, headers=headers, timeout=15)
        if resp2.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(resp2.content)) as z:
                z.extractall(RAW_DIR)
            print(f"[✔] Successfully extracted Travel Reviews archive to {RAW_DIR}")
    except Exception as e:
        pass

    # Inspect what files exist in data/raw
    files = os.listdir(RAW_DIR)
    print(f"[*] Current files in {RAW_DIR}: {files}")
    return files

if __name__ == "__main__":
    download_uci_dataset()
