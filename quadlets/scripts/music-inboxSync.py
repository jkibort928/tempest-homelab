#!/usr/bin/env python3
import os
import subprocess
import re
import shutil
import argparse

# --- CONFIGURATION ---
SPOTIFY_INBOX = "https://open.spotify.com/playlist/38WMKTWNAwebnzPXnqYxQf?si=69885fd60d4e42fa"
YOUTUBE_INBOX = "https://www.youtube.com/playlist?list=PLHq1RrWUkEFUA0ZIcQLo8h86Ybd6wo0L2"

BASE_DIR = os.path.expanduser("~/srv/@music/data")
SPOTIFY_DIR = f"{BASE_DIR}/Mainstream"
YOUTUBE_DIR = f"{BASE_DIR}/Exclusives"

# --- THROTTLING & CHUNKING ---
MAX_YT_DOWNLOADS = 50   # Max YouTube tracks to download per script execution
YT_MIN_SLEEP = 5        # Minimum seconds to pause between YouTube downloads
YT_MAX_SLEEP = 15       # Maximum seconds to pause (randomized to mimic a human)

# Helper to execute system commands cleanly
def run_command(cmd, silent=False):
    print(f"Running: {' '.join(cmd)}")
    
    if silent:
        # Capture output silently for Python to process (e.g., fetching IDs)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error:\n{result.stderr}")
        return result
    else:
        # Stream directly to the terminal for real-time progress bars
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Error: Command exited with status {result.returncode}")
        return result

def sync_spotify():
    print("--- Starting Spotify Sync ---")
    cmd = [
        "spotdl", 
        "download", SPOTIFY_INBOX,
        "--output", f"{SPOTIFY_DIR}/{{artist}} - {{title}}",
        "--archive", f"{SPOTIFY_DIR}/.spotdl_archive",
        "--threads", "1"
    ]
    run_command(cmd)

def sync_youtube():
    print("--- Starting YouTube Sync ---")
    
    # Scan the local directory for existing files
    existing_files = os.listdir(YOUTUBE_DIR)

    # Fetch the video IDs from the YouTube Inbox playlist
    print("Fetching YouTube Inbox playlist IDs...")
    get_ids_cmd = [
        "yt-dlp",
        "--js-runtimes", "node",
        "--flat-playlist", "--get-id", YOUTUBE_INBOX
    ]
    result = run_command(get_ids_cmd, silent=True)
    if result.returncode != 0:
        return
        
    playlist_ids = [vid_id.strip() for vid_id in result.stdout.splitlines() if vid_id.strip()]
    
    # Extract existing ids into a set
    existing_ids = set()
    for filename in existing_files:
        match = re.search(r'\[([a-zA-Z0-9_-]{11})\]\.mp3$', filename)
        if match:
            existing_ids.add(match.group(1))

    # Filter missing IDs in a single pass
    missing_ids = [vid_id for vid_id in playlist_ids if vid_id not in existing_ids]
            
    if not missing_ids:
        print("All YouTube Inbox tracks already exist on disk (matched by ID).")
        return
        
    # Chunking logic
    if len(missing_ids) > MAX_YT_DOWNLOADS:
        print(f"Queue has {len(missing_ids)} missing tracks. Limiting to {MAX_YT_DOWNLOADS} for this run.")
        missing_ids = missing_ids[:MAX_YT_DOWNLOADS]
    else:
        print(f"Found {len(missing_ids)} missing video(s). Initializing download...")
    
    # Download only the missing tracks
    for vid_id in missing_ids:
        cmd = [
            "yt-dlp",
            "--js-runtimes", "node",
            "--min-sleep-interval", str(YT_MIN_SLEEP),
            "--max-sleep-interval", str(YT_MAX_SLEEP),
            "-x", "--audio-format", "mp3",
            "--embed-metadata",     # Injects Title and Artist tags
            "--embed-thumbnail",    # Injects the video thumbnail as Cover Art
            "-o", f"{YOUTUBE_DIR}/%(title)s [%(id)s].%(ext)s",
            f"https://www.youtube.com/watch?v={vid_id}"
        ]
        run_command(cmd)

if __name__ == "__main__":
    # Set up CLI flags
    parser = argparse.ArgumentParser(description="Sync music inboxes from Spotify and YouTube.")
    parser.add_argument("--spotify", action="store_true", help="Sync only the Spotify inbox.")
    parser.add_argument("--yt", action="store_true", help="Sync only the YouTube inbox.")
    args = parser.parse_args()

    run_all = not args.spotify and not args.yt

    # Verify all system and virtual environment dependencies are in PATH
    for tool in ["spotdl", "yt-dlp", "node"]:
        if shutil.which(tool) is None:
            print(f"CRITICAL ERROR: Required dependency '{tool}' not found in PATH.")
            print("Please ensure your virtual environment is active, has the right dependencies, and system runtimes are installed.")
            exit(1)

    for directory in [SPOTIFY_DIR, YOUTUBE_DIR]:
        if not os.path.isdir(directory):
            print(f"Error: Directory does not exist: {directory}")
            exit(1)
    
    if args.spotify or run_all:
        sync_spotify()
        
    if args.yt or run_all:
        sync_youtube()
        
    print("--- Sync Complete ---")
