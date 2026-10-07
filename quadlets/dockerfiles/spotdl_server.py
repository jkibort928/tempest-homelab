from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.background import BackgroundTasks
import subprocess
from datetime import datetime
import os
import glob
import re
import uuid
import asyncio
import signal
import urllib.request
import html as html_lib
from collections import deque

LOG_PATH = "/tmp/spotdl.log"
MUSIC_DIR = "/music"
SPOTIFY_DIR = f"{MUSIC_DIR}/Mainstream"
PLAYLIST_DIR = f"{MUSIC_DIR}/Playlists"

app = FastAPI()

# --- QUEUE & PROCESS MANAGEMENT ---
job_queue = []
job_lock = asyncio.Lock()

def fetch_spotify_playlist_title(url: str) -> str:
    """Scrapes the playlist title from Spotify's Open Graph metadata tag."""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            page_html = response.read().decode('utf-8', errors='ignore')
            
            # Match <meta property="og:title" content="...">
            match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', page_html, re.IGNORECASE)
            if match:
                raw_title = match.group(1)
                # Strip Spotify brand trailing suffixes
                clean_title = re.sub(r'\s*\|\s*Spotify$', '', raw_title, flags=re.IGNORECASE).strip()
                return html_lib.unescape(clean_title)

            # Fallback to <title>
            title_match = re.search(r'<title>(.*?)</title>', page_html, re.IGNORECASE)
            if title_match:
                clean_title = re.sub(r'\s*\|\s*Spotify$', '', title_match.group(1), flags=re.IGNORECASE).strip()
                return html_lib.unescape(clean_title)

    except Exception as e:
        append_log(f"Auto-fetch playlist title failed: {e}")

    # Final fallback if title extraction failed
    playlist_id = url.split("playlist/")[-1].split("?")[0] if "playlist/" in url else "Import"
    return f"Spotify Playlist ({playlist_id[:6]})"

def cleanup_queue():
    """Retains active jobs and trims history to the last 20 completed/canceled entries."""
    global job_queue
    active = [j for j in job_queue if j["status"] in ("queued", "running")]
    history = [j for j in job_queue if j["status"] in ("completed", "canceled")][-20:]
    job_queue = active + history

def append_log(text: str):
    if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 1_000_000:
        with open(LOG_PATH, "w") as f:
            f.write("=== LOG ROTATED ===\n")
    with open(LOG_PATH, "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")

def run_cmd_logged(cmd, description: str, job: dict):
    if job.get("status") == "canceled":
        append_log(f"--- SKIPPED (CANCELED): {description} ---")
        return

    append_log(f"--- START: {description} ---")
    with open(LOG_PATH, "a") as log_file:
        proc = subprocess.Popen(cmd, stdout=log_file, stderr=log_file, text=True, start_new_session=True)
        job["proc"] = proc
        proc.wait()
        job["proc"] = None

    if job.get("status") == "canceled":
        append_log(f"--- CANCELED/TERMINATED: {description} ---\n")
    else:
        append_log(f"--- FINISHED: {description} ---\n")

async def run_serialized_job(job_id: str, task_func, *args):
    async with job_lock:
        job = next((j for j in job_queue if j["id"] == job_id), None)
        if not job or job["status"] == "canceled":
            cleanup_queue()
            return

        job["status"] = "running"
        await asyncio.to_thread(task_func, job, *args)
        if job["status"] == "running":
            job["status"] = "completed"
        
        cleanup_queue()

def enqueue_job(job_type: str, title: str, task_func, *args, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    job = {
        "id": job_id,
        "type": job_type,
        "title": title,
        "status": "queued",
        "created_at": datetime.now().strftime("%H:%M:%S"),
        "proc": None
    }
    job_queue.append(job)
    background_tasks.add_task(run_serialized_job, job_id, task_func, *args)
    return job_id

# --- BACKGROUND TASK WORKERS ---
def run_quick_download(job: dict, url: str, audio_url: str = None):
    target = f"{audio_url}|{url}" if audio_url else url
    cmd = ["spotdl", "download", target, "--output", f"{SPOTIFY_DIR}/{{artist}} - {{title}}"]
    if audio_url:
        cmd.extend(["--overwrite", "force"])

    run_cmd_logged(cmd, f"Single Track Download: {target}", job)

def task_import_playlist(job: dict, name: str, url: str):
    cmd = ["python3", "/app/music-spot-initPlaylist.py", name, url]
    run_cmd_logged(cmd, f"Playlist Import: {name}", job)

def task_resolve_single(job: dict, spotify_url: str, youtube_url: str, playlist_name: str, playlist_url: str):
    if youtube_url and youtube_url.strip():
        target = f"{youtube_url.strip()}|{spotify_url.strip()}"
        cmd = ["spotdl", "download", target, "--output", f"{SPOTIFY_DIR}/{{artist}} - {{title}}", "--overwrite", "force"]
    else:
        target = spotify_url.strip()
        cmd = ["spotdl", "download", target, "--output", f"{SPOTIFY_DIR}/{{artist}} - {{title}}"]
    
    run_cmd_logged(cmd, f"Explicit Remap Download: {spotify_url}", job)
    
    if playlist_name and playlist_url and job.get("status") != "canceled":
        run_cmd_logged(["python3", "/app/music-spot-initPlaylist.py", playlist_name, playlist_url], f"Re-syncing Playlist: {playlist_name}", job)

# --- ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def main_page():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Navidrome Spotify Importer</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { background: #121212; color: #e0e0e0; font-family: sans-serif; margin: 0; padding: 20px; box-sizing: border-box; }
                .layout { display: flex; gap: 20px; max-width: 1200px; margin: 0 auto; flex-wrap: wrap; }
                .main-content { flex: 2; min-width: 320px; }
                .sidebar { flex: 1; min-width: 280px; background: #181818; border-radius: 8px; border: 1px solid #282828; padding: 15px; height: fit-content; }
                
                h2 { color: #1DB954; text-align: center; margin-top: 0; }
                
                .tabs { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #282828; }
                .tab-btn { background: none; border: none; color: #aaa; font-weight: bold; padding: 10px 16px; cursor: pointer; font-size: 15px; }
                .tab-btn.active { color: #1DB954; border-bottom: 3px solid #1DB954; }
                .tab-content { display: none; background: #181818; padding: 20px; border-radius: 8px; border: 1px solid #282828; margin-bottom: 20px; }
                .tab-content.active { display: block; }

                label { display: block; font-size: 13px; color: #b3b3b3; margin-bottom: 5px; font-weight: bold; }
                input[type="text"] { width: 100%; padding: 12px; font-size: 15px; border-radius: 8px; border: 1px solid #333; background: #242424; color: white; box-sizing: border-box; margin-bottom: 12px; }
                button.submit-btn { padding: 12px 24px; font-size: 15px; background: #1DB954; color: white; border: none; border-radius: 25px; font-weight: bold; cursor: pointer; width: 100%; }
                
                .missing-item { background: #222; border-left: 4px solid #e74c3c; padding: 12px; border-radius: 4px; margin-bottom: 10px; }
                .missing-title { font-weight: bold; color: #fff; margin-bottom: 6px; }
                
                pre#log-box { background: #181818; padding: 15px; border-radius: 8px; overflow-y: auto; max-height: 250px; font-family: monospace; font-size: 13px; border: 1px solid #333; white-space: pre-wrap; margin: 0; }
                
                /* Sidebar Queue Styles */
                .queue-item { background: #242424; border: 1px solid #333; border-radius: 6px; padding: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
                .queue-item.running { border-left: 4px solid #1DB954; }
                .queue-item.queued { border-left: 4px solid #f39c12; }
                .queue-item.completed { border-left: 4px solid #3498db; opacity: 0.7; }
                .queue-item.canceled { border-left: 4px solid #e74c3c; opacity: 0.7; }
                .badge { font-size: 10px; text-transform: uppercase; padding: 3px 6px; border-radius: 4px; font-weight: bold; }
                .badge-running { background: #1DB954; color: #000; }
                .badge-queued { background: #f39c12; color: #000; }
                .badge-completed { background: #3498db; color: #fff; }
                .badge-canceled { background: #e74c3c; color: #fff; }
                .cancel-btn { background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: bold; }
                .cancel-btn:hover { background: #c0392b; }
            </style>
        </head>
        <body>
            <h2>Navidrome Spotify Importer</h2>
            <div class="layout">
                <!-- MAIN CONTENT AREA -->
                <div class="main-content">
                    <div class="tabs">
                        <button class="tab-btn active" onclick="switchTab('quick', event)">Quick Download</button>
                        <button class="tab-btn" onclick="switchTab('playlist', event)">Playlist Sync</button>
                        <button class="tab-btn" onclick="switchTab('audit', event)">Missing Audit</button>
                    </div>

                    <div id="tab-quick" class="tab-content active">
                        <form onsubmit="event.preventDefault(); submitForm('/download', this);">
                            <label>Spotify Track / Album URL</label>
                            <input type="text" name="url" placeholder="https://open.spotify.com/track/..." required>
                            <label>Explicit Audio URL (Optional Youtube/Audio Link)</label>
                            <input type="text" name="audio_url" placeholder="https://www.youtube.com/watch?v=...">
                            <button type="submit" class="submit-btn">Download to Server</button>
                        </form>
                    </div>

                    <div id="tab-playlist" class="tab-content">
                        <form onsubmit="event.preventDefault(); submitForm('/import-playlist', this);">
                            <label>Playlist Name <span style="color:#777; font-weight:normal;">(Optional - leave blank to auto-fetch title)</span></label>
                            <input type="text" name="name" placeholder="Leave blank to auto-fetch title from Spotify">
                            <label>Spotify Playlist URL</label>
                            <input type="text" name="url" placeholder="https://open.spotify.com/playlist/..." required>
                            <button type="submit" class="submit-btn">Import & Generate .M3U</button>
                        </form>
                    </div>

                    <div id="tab-audit" class="tab-content">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                            <h3 style="margin:0;">Unresolved Playlist Tracks</h3>
                            <button onclick="loadMissingTracks()" style="background:#333; color:white; border:none; padding:6px 12px; border-radius:4px; cursor:pointer;">Refresh</button>
                        </div>
                        <div id="missing-list">Loading audit...</div>
                    </div>

                    <div style="margin-top: 20px;">
                        <h4 style="margin:5px 0; color:#aaa; font-family:monospace; display:flex; justify-content:space-between;">
                            Live Terminal Output
                            <button onclick="navigator.clipboard.writeText(document.getElementById('log-box').innerText);" style="background:#333; color:white; border:1px solid #555; padding:4px 10px; border-radius:4px; cursor:pointer; font-size:11px;">Copy</button>
                        </h4>
                        <pre id="log-box">Waiting for output...</pre>
                    </div>
                </div>

                <!-- SIDEBAR QUEUE -->
                <div class="sidebar">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <h3 style="margin:0; color:#1DB954; font-size:16px;">Execution Queue</h3>
                        <button onclick="clearHistory()" style="background:#333; color:#aaa; border:1px solid #444; padding:3px 8px; border-radius:4px; cursor:pointer; font-size:11px;">Clear History</button>
                    </div>
                    <div id="queue-list"><p style="color:#777; font-size:13px;">No active or pending jobs.</p></div>
                </div>
            </div>

            <script>
                function switchTab(tabName, evt) {
                    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                    
                    evt.target.classList.add('active');
                    document.getElementById('tab-' + tabName).classList.add('active');
                    if (tabName === 'audit') loadMissingTracks();
                }

                async function submitForm(endpoint, form) {
                    try {
                        const res = await fetch(endpoint, { method: 'POST', body: new FormData(form) });
                        if (!res.ok) {
                            const err = await res.json();
                            alert("Validation Error: " + (err.error || "Failed to submit job."));
                            return;
                        }
                        form.reset();
                        updateQueue();
                    } catch (e) {
                        alert('Connection error occurred.');
                    }
                }

                async function resolveMissing(spotifyUrl, ytInputId, playlistName, playlistUrl) {
                    const ytUrl = document.getElementById(ytInputId).value;
                    const body = new FormData();
                    body.append('spotify_url', spotifyUrl);
                    body.append('youtube_url', ytUrl);
                    body.append('playlist_name', playlistName);
                    body.append('playlist_url', playlistUrl);

                    await fetch('/resolve-missing', { method: 'POST', body: body });
                    updateQueue();
                    setTimeout(loadMissingTracks, 3000);
                }

                async function cancelJob(jobId) {
                    await fetch('/cancel/' + jobId, { method: 'POST' });
                    updateQueue();
                }

                async function clearHistory() {
                    await fetch('/clear-history', { method: 'POST' });
                    updateQueue();
                }

                async function updateQueue() {
                    const container = document.getElementById('queue-list');
                    try {
                        const res = await fetch('/queue');
                        const jobs = await res.json();
                        if (!jobs || jobs.length === 0) {
                            container.innerHTML = '<p style="color:#777; font-size:13px;">No active or pending jobs.</p>';
                            return;
                        }
                        let html = '';
                        jobs.forEach(j => {
                            const isCancelable = j.status === 'queued' || j.status === 'running';
                            html += `
                                <div class="queue-item ${j.status}">
                                    <div>
                                        <div style="font-size:11px; margin-bottom:4px;">
                                            <span class="badge badge-${j.status}">${j.status}</span>
                                            <span style="color:#888; margin-left:5px;">${j.created_at}</span>
                                        </div>
                                        <div style="font-size:13px; font-weight:bold; word-break:break-all;">${j.title}</div>
                                    </div>
                                    ${isCancelable ? `<button class="cancel-btn" onclick="cancelJob('${j.id}')">Cancel</button>` : ''}
                                </div>`;
                        });
                        container.innerHTML = html;
                    } catch (e) {}
                }

                async function loadMissingTracks() {
                    const container = document.getElementById('missing-list');
                    try {
                        const res = await fetch('/missing-tracks');
                        const data = await res.json();
                        if (Object.keys(data).length === 0) {
                            container.innerHTML = '<p style="color:#1DB954;">All playlists 100% matched!</p>';
                            return;
                        }
                        let html = '';
                        let inputIdx = 0;
                        for (const [file, items] of Object.entries(data)) {
                            html += `<h4 style="color:#1DB954;">${items.name} (${items.tracks.length} missing)</h4>`;
                            items.tracks.forEach(t => {
                                const id = 'yt_input_' + inputIdx++;
                                html += `
                                    <div class="missing-item">
                                        <div class="missing-title">${t.track_info}</div>
                                        <div style="display:flex; gap:8px;">
                                            <input type="text" id="${id}" placeholder="Paste YouTube URL override..." style="margin:0; flex:1;">
                                            <button onclick="resolveMissing('${t.spotify_url}', '${id}', '${items.name}', '${items.spotify_playlist_url}')" style="background:#1DB954; color:black; border:none; padding:8px 15px; border-radius:4px; font-weight:bold; cursor:pointer;">Download</button>
                                        </div>
                                    </div>`;
                            });
                        }
                        container.innerHTML = html;
                    } catch (e) {
                        container.innerHTML = '<p style="color:red;">Error loading missing reports.</p>';
                    }
                }

                async function updateLogs() {
                    const box = document.getElementById('log-box');
                    try {
                        let res = await fetch('/log-text');
                        let text = await res.text();
                        const isAtBottom = (box.scrollHeight - box.clientHeight) <= (box.scrollTop + 40);
                        if (box.innerText !== text) {
                            box.innerText = text;
                            if (isAtBottom) box.scrollTop = box.scrollHeight;
                        }
                    } catch (e) {}
                }

                setInterval(() => {
                    updateLogs();
                    updateQueue();
                }, 2000);

                updateLogs();
                updateQueue();
            </script>
        </body>
    </html>
    """

@app.post("/download")
async def start_download(url: str = Form(...), audio_url: str = Form(None), background_tasks: BackgroundTasks = None):
    clean_url = url.strip()
    if "spotify.com/playlist" in clean_url.lower():
        return JSONResponse({"error": "Quick Download is intended for single tracks/albums. Please use the 'Playlist Sync' tab for playlists."}, status_code=400)

    enqueue_job("download", f"Single Download: {clean_url}", run_quick_download, clean_url, audio_url, background_tasks=background_tasks)
    return PlainTextResponse("Enqueued")

@app.post("/import-playlist")
async def import_playlist(name: str = Form(""), url: str = Form(...), background_tasks: BackgroundTasks = None):
    clean_name = name.strip()
    clean_url = url.strip()

    # Protection 1: Check if URL was pasted into Name field
    if re.search(r'https?://', clean_name) or "spotify.com" in clean_name.lower():
        return JSONResponse({"error": "Playlist Name cannot be a URL! Leave it blank to auto-fetch the playlist title."}, status_code=400)

    # Protection 2: Check for valid Spotify Playlist URL
    if "spotify.com/playlist" not in clean_url.lower():
        return JSONResponse({"error": "Playlist URL must be a valid Spotify Playlist link (e.g., open.spotify.com/playlist/...). Track/album links are not allowed here."}, status_code=400)

    # Auto-fetch title if blank
    if not clean_name:
        clean_name = fetch_spotify_playlist_title(clean_url)
        append_log(f"Auto-detected playlist name: '{clean_name}'")

    enqueue_job("playlist", f"Playlist: {clean_name}", task_import_playlist, clean_name, clean_url, background_tasks=background_tasks)
    return PlainTextResponse("Enqueued")

@app.post("/resolve-missing")
async def resolve_missing(spotify_url: str = Form(...), youtube_url: str = Form(""), playlist_name: str = Form(""), playlist_url: str = Form(""), background_tasks: BackgroundTasks = None):
    enqueue_job("remap", f"Remap: {spotify_url}", task_resolve_single, spotify_url, youtube_url, playlist_name, playlist_url, background_tasks=background_tasks)
    return PlainTextResponse("Enqueued")

@app.get("/queue")
async def get_queue():
    sanitized = [
        {
            "id": j["id"],
            "type": j["type"],
            "title": j["title"],
            "status": j["status"],
            "created_at": j["created_at"]
        }
        for j in job_queue
    ]
    return JSONResponse(sanitized)

@app.post("/cancel/{job_id}")
async def cancel_job(job_id: str):
    for job in job_queue:
        if job["id"] == job_id:
            job["status"] = "canceled"
            proc = job.get("proc")
            if proc and proc.poll() is None:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                except (ProcessLookupError, OSError):
                    pass
            cleanup_queue()
            return JSONResponse({"status": "canceled"})
    return JSONResponse({"error": "Job not found"}, status_code=404)

@app.post("/clear-history")
async def clear_history():
    global job_queue
    job_queue = [j for j in job_queue if j["status"] in ("queued", "running")]
    return JSONResponse({"status": "cleared"})

@app.get("/missing-tracks")
async def get_missing_tracks():
    missing_files = glob.glob(f"{PLAYLIST_DIR}/missing_*.txt")
    result = {}
    
    for filepath in missing_files:
        filename = os.path.basename(filepath)
        match = re.search(r'missing_(.+) \[(.+)\]\.txt', filename)
        playlist_name = match.group(1) if match else filename
        playlist_id = match.group(2) if match else ""
        spotify_playlist_url = f"https://open.spotify.com/playlist/{playlist_id}" if playlist_id else ""

        tracks = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith("---") or line.startswith("Format:") or not line.strip():
                    continue
                if "|" in line:
                    info, url = line.strip().split("|", 1)
                    tracks.append({"track_info": info, "spotify_url": url})

        if tracks:
            result[filename] = {
                "name": playlist_name,
                "spotify_playlist_url": spotify_playlist_url,
                "tracks": tracks
            }

    return JSONResponse(result)

@app.get("/log-text", response_class=PlainTextResponse)
async def log_text():
    try:
        with open(LOG_PATH, "r") as f:
            return "".join(deque(f, maxlen=100))
    except FileNotFoundError:
        return "No active or recent operations logged."
