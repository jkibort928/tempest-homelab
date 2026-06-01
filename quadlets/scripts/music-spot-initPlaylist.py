#!/usr/bin/env python3
import os
import subprocess
import argparse
import json
import re
from spotdl.utils.formatter import sanitize_string

# --- CONFIGURATION ---
BASE_DIR = os.path.expanduser("~/srv/@music/data")
PLAYLIST_DIR = f"{BASE_DIR}/Playlists"
SPOTIFY_DIR = f"{BASE_DIR}/Mainstream"
NAVIDROME_MOUNT = "/music"
NAVI_SPOTIFY=f"{NAVIDROME_MOUNT}/Mainstream"

def fetch_metadata(url, temp_file):
    print(f"Fetching playlist metadata from Spotify...")
    cmd = ["spotdl", "save", url, "--save-file", temp_file]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Error fetching metadata. Command exited with status {result.returncode}")
        exit(1)

def build_playlist(name, url):
    os.makedirs(PLAYLIST_DIR, exist_ok=True)

    # Extract the 22-character Spotify ID from the URL
    match = re.search(r'(?:playlist|album|artist)/([a-zA-Z0-9]{22})', url)
    playlist_id = match.group(1) if match else "UNKNOWN_ID"

    m3u_path = f"{PLAYLIST_DIR}/{name} [{playlist_id}].m3u"
    missing_path = f"{PLAYLIST_DIR}/missing_{name} [{playlist_id}].txt"
    temp_json = f"{PLAYLIST_DIR}/temp.spotdl"

    fetch_metadata(url, temp_json)

    with open(temp_json, 'r') as f:
        try:
            track_data = json.load(f)
        except json.JSONDecodeError:
            print("Failed to read spotdl metadata dump.")
            exit(1)

    found_tracks = []
    missing_tracks = []

    print(f"Auditing {len(track_data)} tracks...")

    # Check local storage for each track
    for track in track_data:
        artist = sanitize_string(track.get('artist', 'Unknown'))
        title = sanitize_string(track.get('name', 'Unknown'))
        
        expected_filename = f"{artist} - {title}.mp3"
        
        fullFilePath = os.path.join(SPOTIFY_DIR, expected_filename)
        if os.path.exists(fullFilePath):
            found_tracks.append(f"{NAVI_SPOTIFY}/{expected_filename}")
        else:
            # Grab the Spotify URL from the JSON data
            track_url = track.get('url', 'UNKNOWN_URL')
            missing_tracks.append(f"{artist} - {title}|{track_url}")

    # Write the M3U File
    if found_tracks:
        with open(m3u_path, 'w') as m3u:
            m3u.write("#EXTM3U\n")
            for track_path in found_tracks:
                m3u.write(f"{track_path}\n")
        print("Finished:")
        print(f"Wrote {len(found_tracks)} tracks to {m3u_path}")
        print(f"Wrote {len(missing_tracks)} tracks to {missing_path}")

    # Write the Missing Tracks Report
    if missing_tracks:
        with open(missing_path, 'w') as miss:
            miss.write(f"--- Missing Tracks for {name} ---\n")
            miss.write(f"Format: Artist - Title|Spotify URL\n\n")
            for track in missing_tracks:
                miss.write(f"{track}\n")

    # Cleanup
    if os.path.exists(temp_json):
        os.remove(temp_json)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Navidrome M3U playlists from Spotify URLs.")
    parser.add_argument("name", help="The name of the playlist (wrap in quotes, e.g., \"My Gym Mix\")")
    parser.add_argument("url", help="The Spotify playlist URL")
    args = parser.parse_args()

    build_playlist(args.name, args.url)
