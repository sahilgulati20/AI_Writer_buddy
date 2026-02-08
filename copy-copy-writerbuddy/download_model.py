#!/usr/bin/env python3
"""Download and extract a Vosk Indian English model into ./model/en_in

Usage:
  python3 download_model.py
"""
import os
import shutil
import sys
from pathlib import Path

MODEL_URL_SMALL = "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip"
MODEL_URL_LARGE = "https://alphacephei.com/vosk/models/vosk-model-en-in-0.5.zip"

TARGET_DIR = Path("./model/en_in")
TMP_ZIP = Path("./model_tmp.zip")


def download():
    import requests, zipfile, io

    print("\n--- Vosk Model Downloader ---\n")
    print("1. Small Model (36MB)  - Fast, good for basic commands")
    print("2. Large Model (1GB)   - High accuracy, better for dictation")
    print("\nChoose your model (1 or 2): ", end="")
    
    choice = input().strip()
    if choice == "2":
        model_url = MODEL_URL_LARGE
        print(f"\nSelected: LARGE model. This may take a while to download...")
    else:
        model_url = MODEL_URL_SMALL
        print(f"\nSelected: SMALL model.")

    if TARGET_DIR.exists():
        print(f"Warning: A model already exists at {TARGET_DIR}")
        print("It will be replaced. Continue? (y/n): ", end="")
        if input().lower() != 'y':
            print("Aborted.")
            return

    print("\nDownloading model from", model_url)
    try:
        r = requests.get(model_url, stream=True)
        r.raise_for_status()
        
        # Get total file size for progress bar usually found in headers
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        
        with open(TMP_ZIP, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        done = int(50 * downloaded / total_size)
                        sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded//1024//1024}MB / {total_size//1024//1024}MB")
                        sys.stdout.flush()
        print("\nDownload complete.")

    except Exception as e:
        print(f"\nError downloading: {e}")
        return

    print("Extracting...")
    try:
        with zipfile.ZipFile(TMP_ZIP, 'r') as z:
            # Extract into ./model
            extract_dir = Path("./model")
            extract_dir.mkdir(parents=True, exist_ok=True)
            z.extractall(path=extract_dir)

        # Rename the extracted folder to 'en_in'
        # Large model extracts to 'vosk-model-en-in-0.5', small to 'vosk-model-small-en-in-0.4'
        for child in extract_dir.iterdir():
            if child.is_dir() and child.name.startswith("vosk-model"):
                if TARGET_DIR.exists():
                    shutil.rmtree(TARGET_DIR)
                child.rename(TARGET_DIR)
                print(f"Model installed to {TARGET_DIR}")
                break
    except Exception as e:
        print(f"Error extracting: {e}")
    finally:
        if TMP_ZIP.exists():
            TMP_ZIP.unlink()

    print("\nModel ready! Restart your main program to use it.")


if __name__ == '__main__':
    try:
        download()
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print("Download failed:", e)
        sys.exit(2)
