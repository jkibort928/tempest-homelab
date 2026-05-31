#!/usr/bin/env python3
import os
import subprocess
import re
import shutil

# --- CONFIGURATION ---
SPOTIFY_INBOX = "https://open.spotify.com/playlist/38WMKTWNAwebnzPXnqYxQf?si=69885fd60d4e42fa"
YOUTUBE_INBOX = "https://www.youtube.com/playlist?list=PLHq1RrWUkEFUA0ZIcQLo8h86Ybd6wo0L2"

BASE_DIR = os.path.expanduser("~/srv/@music/data")
SPOTIFY_DIR = f"{BASE_DIR}/Mainstream"
YOUTUBE_DIR = f"{BASE_DIR}/Exclusives"

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
        "--output", f"{SPOTIFY_DIR}/{{artist}} - {{title}}"
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
    
    # Download only the missing tracks
    for vid_id in missing_ids:
        cmd = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "-o", f"{YOUTUBE_DIR}/%(title)s [%(id)s].%(ext)s",
            f"https://www.youtube.com/watch?v={vid_id}"
        ]
        run_command(cmd)

if __name__ == "__main__":
    for tool in ["spotdl", "yt-dlp"]:
        if shutil.which(tool) is None:
            print(f"Error: '{tool}' not found in PATH.")
            print("Did you forget to activate your virtual environment? (source .venv/bin/activate)")
            print("(Ensure spotdl and yt-dlp are installed through pip in the venv too!)")
            exit(1)

    for directory in [SPOTIFY_DIR, YOUTUBE_DIR]:
        if not os.path.isdir(directory):
            print(f"Error: Directory does not exist: {directory}")
            exit(1)
    
    sync_spotify()
    sync_youtube()
    print("--- Sync Complete ---")
