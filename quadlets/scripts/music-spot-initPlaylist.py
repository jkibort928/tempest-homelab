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

def check_local_files(track_data):
    found = []
    missing = []
    for track in track_data:
        artist = sanitize_string(track.get('artist', 'Unknown'))
        title = sanitize_string(track.get('name', 'Unknown'))
        expected_filename = f"{artist} - {title}.mp3"
        fullFilePath = os.path.join(SPOTIFY_DIR, expected_filename)
        
        if os.path.exists(fullFilePath):
            found.append(f"{NAVI_SPOTIFY}/{expected_filename}")
        else:
            track_url = track.get('url', 'UNKNOWN_URL')
            missing.append(f"{artist} - {title}|{track_url}")
    return found, missing

def build_playlist(name, url):
    os.makedirs(PLAYLIST_DIR, exist_ok=True)

    # Extract the 22-character Spotify ID from the URL
    match = re.search(r'(?:playlist|album|artist)/([a-zA-Z0-9]{22})', url)
    playlist_id = match.group(1) if match else "UNKNOWN_ID"

    m3u_path = f"{PLAYLIST_DIR}/{name} [{playlist_id}].m3u"
    missing_path = f"{PLAYLIST_DIR}/missing_{name} [{playlist_id}].txt"
    temp_json = f"{PLAYLIST_DIR}/temp_{playlist_id}.spotdl"

    try:
        fetch_metadata(url, temp_json)

        with open(temp_json, 'r') as f:
            try:
                track_data = json.load(f)
            except json.JSONDecodeError:
                print("Failed to read spotdl metadata dump.")
                exit(1)

        print(f"Auditing {len(track_data)} tracks...")
            
        # Pass 1: See what we already have
        found_tracks, missing_tracks = check_local_files(track_data)

        # Pass 2: Download anything missing
        if missing_tracks:
            print(f"\nAttempting to automatically download {len(missing_tracks)} missing tracks...")
            
            urls_to_download = [track.split("|")[1] for track in missing_tracks]
            
            chunk_size = 15
            total_chunks = (len(urls_to_download) + chunk_size - 1) // chunk_size
            
            for i in range(0, len(urls_to_download), chunk_size):
                chunk = urls_to_download[i:i + chunk_size]
                current_chunk = (i // chunk_size) + 1
                
                print(f"\n>> Processing Batch {current_chunk} of {total_chunks} ({len(chunk)} tracks)...")
                cmd = ["spotdl", "download"] + chunk + ["--output", f"{SPOTIFY_DIR}/{{artist}} - {{title}}"]
                subprocess.run(cmd)
                
            # Pass 3: Re-audit to see what failed
            print("\nRe-auditing library after download phase...")
            found_tracks, missing_tracks = check_local_files(track_data)

        # Write the M3U File
        if found_tracks:
            with open(m3u_path, 'w') as m3u:
                m3u.write("#EXTM3U\n")
                for track_path in found_tracks:
                    m3u.write(f"{track_path}\n")
            print("Finished:")
            print(f"Wrote {len(found_tracks)} tracks to {m3u_path}")

        # Write the Missing Tracks Report
        if missing_tracks:
            with open(missing_path, 'w') as miss:
                miss.write(f"--- Missing Tracks for {name} ---\n")
                miss.write(f"Format: Artist - Title|Spotify URL\n\n")
                for track in missing_tracks:
                    miss.write(f"{track}\n")
            print(f"Wrote {len(missing_tracks)} tracks to {missing_path}")
        else:
            # 100% complete! Clean up the old report if it exists from a previous run
            if os.path.exists(missing_path):
                os.remove(missing_path)
                print(f"Cleaned up old missing tracks report: {os.path.basename(missing_path)}")

    except KeyboardInterrupt:
        print("\n\nProcess aborted by user (Ctrl+C).")
        print("Downloads stopped. Playlist generation skipped.")

    finally:
        # Cleanup
        if os.path.exists(temp_json):
            os.remove(temp_json)
            print(f"Cleaned up temporary file: {temp_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Navidrome M3U playlists from Spotify URLs.")
    parser.add_argument("name", help="The name of the playlist (wrap in quotes, e.g., \"My Gym Mix\")")
    parser.add_argument("url", help="The Spotify playlist URL")
    args = parser.parse_args()

    build_playlist(args.name, args.url)
