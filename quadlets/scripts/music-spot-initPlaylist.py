#!/usr/bin/env python3
import os
import subprocess
import argparse
import re
from spotdl.utils.formatter import sanitize_string
from spotdl.types.playlist import Playlist
from spotdl.utils.spotify import SpotifyClient
from dotenv import load_dotenv

# --- CONFIGURATION ---
BASE_DIR = os.path.expanduser("~/srv/@music/data")
PLAYLIST_DIR = f"{BASE_DIR}/Playlists"
SPOTIFY_DIR = f"{BASE_DIR}/Mainstream"
NAVIDROME_MOUNT = "/music"
NAVI_SPOTIFY=f"{NAVIDROME_MOUNT}/Mainstream"

def audit_local_storage(songs):
    """Checks local disk and returns found tracks, missing URLs, and report lines."""
    found = []
    missing_links = []
    report_lines = []
    
    for song in songs:
        artist = sanitize_string(song.artist)
        title = sanitize_string(song.name)
        expected_filename = f"{artist} - {title}.mp3"
        full_file_path = os.path.join(SPOTIFY_DIR, expected_filename)

        if os.path.exists(full_file_path):
            found.append(f"{NAVI_SPOTIFY}/{expected_filename}")
        else:
            missing_links.append(song.url)
            report_lines.append(f"{artist} - {title}|{song.url}")
            
    return found, missing_links, report_lines

def build_playlist(name, url):
    os.makedirs(PLAYLIST_DIR, exist_ok=True)

    # 1. Load the specific .env file 
    # (Looks for .env.spotify in the same directory as this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env.spotify")
    load_dotenv(dotenv_path=env_path)

    # 2. Extract the 22-character Spotify ID from the URL
    match = re.search(r'(?:playlist|album|artist)/([a-zA-Z0-9]{22})', url)
    playlist_id = match.group(1) if match else "UNKNOWN_ID"

    m3u_path = f"{PLAYLIST_DIR}/{name} [{playlist_id}].m3u"
    missing_path = f"{PLAYLIST_DIR}/missing_{name} [{playlist_id}].txt"

    print(f"Initializing Official Spotify API Client...")
    
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(f"Error: SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not found in {env_path}")
        exit(1)

    SpotifyClient.init(
        client_id=client_id,
        client_secret=client_secret,
        user_auth=True
    )

    try:
        print(f"Fetching playlist metadata...")
        playlist = Playlist.from_url(url)
        songs = playlist.songs
        
        # Guard against Spotify returning an empty track list for unowned public lists
        if not songs:
            print("\nError: Playlist returned 0 tracks.")
            print("Reminder: If this is a public playlist you don't own, Spotify's API lockdown requires you to copy/clone the tracks into a playlist on your own account.")
            exit(1)
            
    except Exception as e:
        print(f"\nError fetching Spotify playlist natively: {e}")
        print("Reminder: If this is a public playlist you don't own, Spotify's API lockdown requires you to copy/clone the tracks into a playlist on your own account.")
        exit(1)

    print(f"Auditing {len(songs)} tracks against local storage...")

    # Pass 1: Local disk check
    found_tracks, missing_urls, missing_report_lines = audit_local_storage(songs)

    # Pass 2: Download phase for missing files
    if missing_urls:
        print(f"\nFound {len(missing_urls)} missing tracks. Launching spotDL...")
        
        chunk_size = 15
        total_chunks = (len(missing_urls) + chunk_size - 1) // chunk_size
        
        try:
            for i in range(0, len(missing_urls), chunk_size):
                chunk = missing_urls[i:i + chunk_size]
                current_chunk = (i // chunk_size) + 1
                
                print(f">> Processing Batch {current_chunk} of {total_chunks} ({len(chunk)} tracks)...")
                cmd = ["spotdl", "download"] + chunk + ["--output", f"{SPOTIFY_DIR}/{{artist}} - {{title}}"]
                subprocess.run(cmd)
        
        except KeyboardInterrupt:
            print("\n\nProcess aborted by user (Ctrl+C). Saving current progress...")
        
        # Pass 3: Final re-audit to verify what successfully made it to disk
        print("\nRe-auditing library after download phase...")
        found_tracks, _, missing_report_lines = audit_local_storage(songs)

    # Build the final M3U file natively
    if found_tracks:
        with open(m3u_path, 'w') as m3u:
            m3u.write("#EXTM3U\n")
            for track_path in found_tracks:
                m3u.write(f"{track_path}\n")
        print(f"\nGenerated Navidrome-compatible playlist: {m3u_path}")

    # 3. Write or cleanup the missing report
    if missing_report_lines:
        with open(missing_path, 'w') as miss:
            miss.write(f"--- Missing Tracks for {name} ---\n")
            miss.write(f"Format: Artist - Title|Spotify URL\n\n")
            for track in missing_report_lines:
                miss.write(f"{track}\n")
        print(f"Wrote {len(missing_report_lines)} tracks to {missing_path}")
    else:
        if os.path.exists(missing_path):
            os.remove(missing_path)
            print(f"Cleaned up old missing tracks report: {missing_path}")
        print("All tracks synced! No missing tracks detected.")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Navidrome M3U playlists from Spotify URLs.")
    parser.add_argument("name", help="The name of the playlist (wrap in quotes, e.g., \"My Gym Mix\")")
    parser.add_argument("url", help="The Spotify playlist URL")
    args = parser.parse_args()

    build_playlist(args.name, args.url)
