from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.background import BackgroundTasks
import subprocess
from datetime import datetime
import os
from collections import deque

LOG_PATH = "/tmp/spotdl.log"

app = FastAPI()

def run_download(url: str):
    if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 1_000_000:
        with open(LOG_PATH, "w") as f:
            f.write("=== LOG AUTOMATICALLY ROTATED TO CONSERVE SPACE ===\n")

    with open(LOG_PATH, "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"\n\n========================================\n")
        log_file.write(f"QUEUE JOB STARTED AT: {timestamp}\n")
        log_file.write(f"TARGET URL: {url}\n")
        log_file.write(f"========================================\n\n")
        log_file.flush()

        subprocess.run(
            ["spotdl", "download", url, "--output", "/music/{artist} - {title}"],
            stdout=log_file,
            stderr=log_file,
            text=True
        )

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
            <form action="/download" method="post">
                <input type="text" name="url" style="width:90%; max-width:500px; padding:12px; font-size:16px; border-radius:8px; border:1px solid #333; background:#181818; color:white;" placeholder="Paste Spotify Track, Album, or Playlist URL..." required><br><br>
                <button type="submit" style="padding:12px 24px; font-size:16px; background:#1DB954; color:white; border:none; border-radius:25px; font-weight:bold; cursor:pointer;">Download to Server</button>
            </form>
        </body>
    </html>
    """

@app.post("/download", response_class=HTMLResponse)
async def start_download(url: str = Form(...), background_tasks: BackgroundTasks = None):
    background_tasks.add_task(run_download, url)
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
