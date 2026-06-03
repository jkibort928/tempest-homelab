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

    # Initialize a queue to hold all matched pairs
    download_queue = []

    for i, line in enumerate(lines):
        # Skip headers and empty lines
        if line.startswith("---") or line.startswith("Format:") or not line.strip():
            continue

        if "|" not in line:
            continue

        track_info, spot_url = line.strip().split("|", 1)
        
        # Smart Check: Skip if already present
        expected_filename = f"{track_info}.mp3"
        if os.path.exists(os.path.join(SPOTIFY_DIR, expected_filename)):
            continue
        
        print(f"Missing: {track_info} ({i}/{len(lines)})")
        yt_url = input("YouTube URL (or hit Enter to skip): ").strip()

        if not yt_url:
            print("Skipped input.\n")
            continue

        # Queue the query for later processing
        download_queue.append((track_info, f"{yt_url}|{spot_url}"))
        print("Queued!\n")

    # Phase 2: Process the collected queue sequentially
    if not download_queue:
        print("No tracks were added to the download queue.")
        return

    total_tracks = len(download_queue)
    print(f"--- Input Collection Complete ---")
    print(f"Starting sequential download of {total_tracks} tracks.")

    for index, (track_info, query) in enumerate(download_queue, 1):
        print(f"[{index}/{total_tracks}] Downloading: {track_info}")
        
        cmd = [
            "spotdl", 
            "download", query,
            "--output", f"{SPOTIFY_DIR}/{{artist}} - {{title}}"
        ]
        
        # Run the download blocking task
        subprocess.run(cmd)
        print(f"Finished [{index}/{total_tracks}]\n")

    print("--- All Queued Downloads Complete ---")
    print("Re-run your playlist init script to regenerate the Navidrome .m3u map and update/remove the missing list.")

if __name__ == "__main__":
    if shutil.which("spotdl") is None:
        print("Error: spotdl not found. Did you activate your virtual environment?")
        exit(1)
        
    if len(sys.argv) < 2:
        print("Usage: ./fix_missing.py <path_to_missing_tracks.txt>")
        exit(1)
        
    process_missing_file(sys.argv[1])
