#!/usr/bin/env python3
import sys
import os
import subprocess
import shutil

# --- CONFIGURATION ---
SPOTIFY_DIR = os.path.expanduser("~/srv/@music/data/Mainstream")

def process_missing_file(filepath):
    if not os.path.isfile(filepath):
        print(f"Error: File not found - {filepath}")
        return

    with open(filepath, 'r') as f:
        lines = f.readlines()

    print("--- SpotDL Batch Matcher ---")
    print("Paste a YouTube link and press Enter.")
    print("Leave blank and press Enter to skip.\n")

    for line in lines:
        # Skip headers and empty lines
        if line.startswith("---") or line.startswith("Format:") or not line.strip():
            continue

        if "|" not in line:
            continue

        track_info, spot_url = line.strip().split("|", 1)
        
        # Avoid already found tracks
        expected_filename = f"{track_info}.mp3"
        if os.path.exists(os.path.join(SPOTIFY_DIR, expected_filename)):
            continue
        
        print(f"\nMissing: {track_info}")
        yt_url = input("YouTube URL (or hit Enter to skip): ").strip()

        if not yt_url:
            print("Skipping...")
            continue

        query = f"{yt_url}|{spot_url}"
        
        cmd = [
            "spotdl", 
            "download", query,
            "--output", f"{SPOTIFY_DIR}/{{artist}} - {{title}}"
        ]
        
        print("Downloading...")
        subprocess.run(cmd)

if __name__ == "__main__":
    if shutil.which("spotdl") is None:
        print("Error: spotdl not found. Did you activate your virtual environment?")
        exit(1)
        
    if len(sys.argv) < 2:
        print("Usage: ./fix_missing.py <path_to_missing_tracks.txt>")
        exit(1)
        
    process_missing_file(sys.argv[1])
