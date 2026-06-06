from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.background import BackgroundTasks
import subprocess
from datetime import datetime
import os
from collections import deque

LOG_PATH = "/tmp/spotdl.log"

app = FastAPI()

def run_download(url: str, audio_url: str = None):
    log_path = "/tmp/spotdl.log"
    
    if os.path.exists(log_path) and os.path.getsize(log_path) > 1_000_000:
        with open(log_path, "w") as f:
            f.write("=== LOG AUTOMATICALLY ROTATED TO CONSERVE SPACE ===\n")

    target = f"{audio_url}|{url}" if audio_url else url
    
    cmd = ["spotdl", "download", target, "--output", "/music/{artist} - {title}"]
    if audio_url:
        cmd.extend(["--overwrite", "force"])

    with open(log_path, "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"\n\n========================================\n")
        log_file.write(f"QUEUE JOB STARTED AT: {timestamp}\n")
        log_file.write(f"TARGET: {target}\n")
        if audio_url:
            log_file.write(f"MODE: Explicit Audio Remap (Force Overwrite)\n")
        log_file.write(f"========================================\n\n")
        log_file.flush()

        subprocess.run(cmd, stdout=log_file, stderr=log_file, text=True)

@app.get("/", response_class=HTMLResponse)
async def main_page():
    return """
    <html>
        <head>
            <title>Spotify Downloader</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="background:#121212; color:white; font-family:sans-serif; text-align:center; padding:10% 5%;">
            <h2 style="color:#1DB954; font-size:28px; margin-bottom:20px;">Navidrome Spotify Link Importer</h2>
            
            <form action="/download" method="post" style="display: flex; flex-direction: column; align-items: center; gap: 15px; width: 100%;">
                <div style="width: 90%; max-width: 500px; text-align: left;">
                    <label style="color: #aaa; font-size: 14px; display: block; margin-bottom: 5px;">Spotify Link (Required)</label>
                    <input type="text" name="url" style="width:100%; padding:12px; font-size:16px; border-radius:8px; border:1px solid #333; background:#181818; color:white;" placeholder="Paste Spotify Track, Album, or Playlist URL..." required>
                </div>
                
                <div style="width: 90%; max-width: 500px; text-align: left;">
                    <label style="color: #aaa; font-size: 14px; display: block; margin-bottom: 5px;">Explicit Audio Link (Optional YouTube/SoundCloud)</label>
                    <input type="text" name="audio_url" style="width:100%; padding:12px; font-size:16px; border-radius:8px; border:1px solid #333; background:#181818; color:white;" placeholder="Paste specific video URL to fix or override source...">
                </div>
                
                <button type="submit" style="padding:12px 24px; font-size:16px; background:#1DB954; color:white; border:none; border-radius:25px; font-weight:bold; cursor:pointer; margin-top: 10px;">Download to Server</button>
            </form>
            
            <br><br>
            <a href="/status" style="color:#aaa; text-decoration:none; font-size:14px; border:1px solid #333; padding:8px 16px; border-radius:20px; background:#181818; display:inline-block; margin-top:10px;">View Live Progress & Logs &rarr;</a>
        </body>
    </html>
    """

@app.post("/download", response_class=HTMLResponse)
async def start_download(url: str = Form(...), audio_url: str = Form(None), background_tasks: BackgroundTasks = None):
    background_tasks.add_task(run_download, url, audio_url)
    return """
    <body style="background:#121212; color:white; font-family:sans-serif; text-align:center; padding-top:10%;">
        <h3 style="color:#1DB954;">Download dispatched to background thread!</h3>
        <br><br>
        <a href="/status" style="padding:12px 24px; background:#1DB954; color:white; text-decoration:none; border-radius:25px; font-weight:bold;">View Live Progress</a>
        <br><br><br>
        <a href="/" style="color:#aaa; text-decoration:none;">&larr; Go Back Home</a>
    </body>
    """

@app.get("/log-text", response_class=PlainTextResponse)
async def log_text():
    try:
        with open(LOG_PATH, "r") as f:
            return "".join(deque(f, maxlen=100))
    except FileNotFoundError:
        return "No active or recent downloads found."

@app.get("/status", response_class=HTMLResponse)
async def status_page():
    return """
    <html>
        <head>
            <title>Download Status</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="background:#121212; color:white; font-family:monospace; padding:20px;">
            <h3 style="color:#1DB954;">
                <a href="/" style="color:#1DB954; text-decoration:none;">&larr; Home</a> | Live Progress
                <button onclick="navigator.clipboard.writeText(document.getElementById('log-box').innerText); alert('Copied!');" style="margin-left:15px; background:#333; color:white; border:1px solid #555; padding:6px 12px; border-radius:4px; cursor:pointer; font-size:12px;">Copy Logs</button>
            </h3>
            <pre id="log-box" style="background:#181818; padding:15px; border-radius:8px; text-align:left; overflow-x:auto; white-space:pre-wrap; font-size:14px; border:1px solid #333;">Loading active logs...</pre>

            <script>
                async function updateLogs() {
                    try {
                        let res = await fetch('/log-text');
                        let text = await res.text();
                        let box = document.getElementById('log-box');
                        if (box.innerText !== text) {
                            box.innerText = text;
                        }
                    } catch (e) {}
                }
                // Silently refresh the text container every 3 seconds without refreshing the document shell
                setInterval(updateLogs, 3000);
                updateLogs();
            </script>
        </body>
    </html>
    """
