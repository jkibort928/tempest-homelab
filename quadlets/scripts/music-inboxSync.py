#!/usr/bin/env python3
import os
import subprocess
import re

# --- CONFIGURATION ---
SPOTIFY_INBOX = "https://open.spotify.com/playlist/38WMKTWNAwebnzPXnqYxQf?si=69885fd60d4e42fa"
YOUTUBE_INBOX = "https://www.youtube.com/playlist?list=PLHq1RrWUkEFUA0ZIcQLo8h86Ybd6wo0L2"

BASE_DIR = os.path.expanduser("~/srv/@music/data")
SPOTIFY_DIR = f"{BASE_DIR}/Mainstream"
YOUTUBE_DIR = f"{BASE_DIR}/Exclusives"

# Helper to execute system commands cleanly
def run_command(cmd, silent=False):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error:\n{result.stderr}")
    elif not silent and result.stdout.strip():
        print(result.stdout)
    return result

def sync_spotify():
    print("--- Starting Spotify Sync ---")
    # Using the official spotdl container image
    cmd = [
        "podman", "run", "--rm",
        "-v", f"{SPOTIFY_DIR}:/music:z",
        "docker.io/spotdl/spotify-downloader:latest",
        "sync", SPOTIFY_INBOX,
        "--output", "/music/{artist} - {title}.{ext}"
    ]
    run_command(cmd)

def sync_youtube():
    print("--- Starting YouTube Sync ---")
    
    # Scan the local directory for existing files
    existing_files = os.listdir(YOUTUBE_DIR)

    # Fetch the video IDs from the YouTube Inbox playlist
    print("Fetching YouTube Inbox playlist IDs...")
    get_ids_cmd = [
        "podman", "run", "--rm",
        "ghcr.io/jauderho/yt-dlp:latest",
        "--flat-playlist", "--get-id", YOUTUBE_INBOX
    ]
    result = run_command(get_ids_cmd, silent=True)
    if result.returncode != 0:
        return
        
    playlist_ids = [vid_id.strip() for vid_id in result.stdout.splitlines() if vid_id.strip()]
    
    # Extract existing ids into a set
    existing_ids = set()
    for filename in existing_files:
        match = re.search(r'\[([a-zA-Z0-9_-]{11})\]\.[^.]+$', filename)
        if match:
            existing_ids.add(match.group(1))

    # Filter missing IDs in a single pass
    missing_ids = [vid_id for vid_id in playlist_ids if vid_id not in existing_ids]
            
    if not missing_ids:
        print("All YouTube Inbox tracks already exist on disk (matched by ID).")
        return
        
    print(f"Found {len(missing_ids)} missing video(s). Initializing download...")
    
    # Explicitly download only the verified missing tracks
    for vid_id in missing_ids:
        cmd = [
            "podman", "run", "--rm",
            "-v", f"{YOUTUBE_DIR}:/music:z",  # Fixed variable name here
            "ghcr.io/jauderho/yt-dlp:latest",
            "-x", "--audio-format", "mp3",
            "-o", "/music/%(title)s [%(id)s].%(ext)s",
            f"https://www.youtube.com/watch?v={vid_id}"
        ]
        run_command(cmd)

if __name__ == "__main__":
    if not os.path.isdir(SPOTIFY_DIR):
        print(f"Error: Spotify directory does not exist: {SPOTIFY_DIR}")
        exit(1)

    if not os.path.isdir(YOUTUBE_DIR):
        print(f"Error: Youtube directory does not exist: {YOUTUBE_DIR}")
        exit(1)
    
    sync_spotify()
    sync_youtube()
    print("--- Sync Complete ---")
