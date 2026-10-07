#!/usr/bin/env python3
import os
import subprocess
import argparse
import json
import re
from spotdl.utils.formatter import sanitize_string

# --- CONFIGURATION ---
BASE_DIR = os.getenv("MUSIC_BASE_DIR", "/music" if os.path.exists("/music") else "/mnt/storage/music")
PLAYLIST_DIR = f"{BASE_DIR}/Playlists"
SPOTIFY_DIR = f"{BASE_DIR}/Mainstream"
NAVIDROME_MOUNT = "/music"
NAVI_SPOTIFY = f"{NAVIDROME_MOUNT}/Mainstream"

def fetch_metadata(url, temp_file):
    print(f"Fetching playlist metadata from Spotify...")
    cmd = ["spotdl", "save", url, "--save-file", temp_file, "--log-level", "INFO"]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Error fetching metadata. Command exited with status {result.returncode}")
        exit(1)

def check_local_files(track_data):
    found = []
    missing = []
    for track in track_data:
        artists = track.get('artists', [])
        raw_artist = artists[0] if artists else track.get('artist', 'Unknown')
        
        artist = sanitize_string(raw_artist)
        title = sanitize_string(track.get('name', 'Unknown'))
        expected_filename = f"{artist} - {title}.mp3"
        fullFilePath = os.path.join(SPOTIFY_DIR, expected_filename)
        
        if os.path.exists(fullFilePath):
            found.append(f"{NAVI_SPOTIFY}/{expected_filename}")
        else:
            track_url = track.get('url', 'UNKNOWN_URL')
            missing.append(f"{artist} - {title}|{track_url}")
    return found, missing

def write_playlist_and_missing(name, playlist_id, found_tracks, missing_tracks):
    """Always writes the M3U and missing report immediately."""
    os.makedirs(PLAYLIST_DIR, exist_ok=True)
    m3u_path = f"{PLAYLIST_DIR}/{name} [{playlist_id}].m3u"
    missing_path = f"{PLAYLIST_DIR}/missing_{name} [{playlist_id}].txt"

    # 1. ALWAYS write/update the M3U file immediately
    with open(m3u_path, 'w') as m3u:
        m3u.write("#EXTM3U\n")
        for track_path in found_tracks:
            m3u.write(f"{track_path}\n")
    print(f"Wrote {len(found_tracks)} existing tracks to {m3u_path}")

    # 2. Write or clean up the Missing Tracks report
    if missing_tracks:
        with open(missing_path, 'w') as miss:
            miss.write(f"--- Missing Tracks for {name} ---\n")
            miss.write(f"Format: Artist - Title|Spotify URL\n\n")
            for track in missing_tracks:
                miss.write(f"{track}\n")
        print(f"Wrote {len(missing_tracks)} missing tracks to {missing_path}")
    else:
        if os.path.exists(missing_path):
            os.remove(missing_path)
            print(f"All tracks 100% matched! Removed missing report: {os.path.basename(missing_path)}")

def build_playlist(name, url):
    os.makedirs(PLAYLIST_DIR, exist_ok=True)
    os.makedirs(SPOTIFY_DIR, exist_ok=True)

    match = re.search(r'(?:playlist|album|artist)/([a-zA-Z0-9]{22})', url)
    playlist_id = match.group(1) if match else "UNKNOWN_ID"
    temp_json = f"{PLAYLIST_DIR}/temp_{playlist_id}.spotdl"

    fetch_metadata(url, temp_json)

    with open(temp_json, 'r') as f:
        try:
            track_data = json.load(f)
        except json.JSONDecodeError:
            print("Failed to read spotdl metadata dump.")
            exit(1)

    print(f"Auditing {len(track_data)} tracks...")
        
    # Phase 1: Local Audit
    found_tracks, missing_tracks = check_local_files(track_data)

    # Phase 2: Instant M3U & Missing TXT Generation
    write_playlist_and_missing(name, playlist_id, found_tracks, missing_tracks)

    # Phase 3: Auto-download missing tracks without touching existing files
    if missing_tracks:
        print(f"\nAttempting automatic download for {len(missing_tracks)} missing tracks...")
        urls_to_download = [track.split("|")[1] for track in missing_tracks]
        
        chunk_size = 15
        for i in range(0, len(urls_to_download), chunk_size):
            chunk = urls_to_download[i:i + chunk_size]
            # Use skip-existing behavior, no force overwrite
            cmd = ["spotdl", "download"] + chunk + ["--output", f"{SPOTIFY_DIR}/{{artist}} - {{title}}"]
            subprocess.run(cmd)
        
        # Phase 4: Final Re-Audit to pick up newly downloaded tracks
        print("\nRe-auditing library after download phase...")
        found_tracks, missing_tracks = check_local_files(track_data)
        write_playlist_and_missing(name, playlist_id, found_tracks, missing_tracks)

    # Cleanup
    if os.path.exists(temp_json):
        os.remove(temp_json)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Navidrome M3U playlists from Spotify URLs.")
    parser.add_argument("name", help="The name of the playlist")
    parser.add_argument("url", help="The Spotify playlist URL")
    args = parser.parse_args()

    build_playlist(args.name, args.url)
