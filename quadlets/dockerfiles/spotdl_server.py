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
        <body style="background:#121212; color:white; font-family:sans-serif; margin:0; padding:20px; display:flex; flex-direction:column; height:100vh; box-sizing:border-box;">
            
            <div style="flex:0 0 auto; text-align:center; padding-bottom:20px;">
                <h2 style="color:#1DB954; font-size:24px; margin:0 0 15px 0;">Navidrome Spotify Importer</h2>
                
                <form onsubmit="event.preventDefault(); startDownload(this);" style="display:flex; flex-direction:column; align-items:center; gap:12px; width:100%;">
                    <div style="width:100%; max-width:500px; text-align:left;">
                        <input type="text" name="url" style="width:100%; padding:12px; font-size:16px; border-radius:8px; border:1px solid #333; background:#181818; color:white; box-sizing:border-box;" placeholder="Spotify URL..." required>
                    </div>
                    <div style="width:100%; max-width:500px; text-align:left;">
                        <input type="text" name="audio_url" style="width:100%; padding:12px; font-size:16px; border-radius:8px; border:1px solid #333; background:#181818; color:white; box-sizing:border-box;" placeholder="Explicit Audio URL (Optional)...">
                    </div>
                    <button type="submit" style="padding:12px 24px; font-size:16px; background:#1DB954; color:white; border:none; border-radius:25px; font-weight:bold; cursor:pointer;">Download to Server</button>
                </form>
            </div>
            
            <div style="flex:1 1 auto; display:flex; flex-direction:column; min-height:0;">
                <h4 style="margin:5px 0; color:#aaa; font-family:monospace; display:flex; justify-content:space-between; align-items:center;">
                    Live Terminal Output 
                    <button onclick="navigator.clipboard.writeText(document.getElementById('log-box').innerText); alert('Copied!');" style="background:#333; color:white; border:1px solid #555; padding:4px 10px; border-radius:4px; cursor:pointer; font-size:11px;">Copy</button>
                </h4>
                <pre id="log-box" style="flex:1; background:#181818; padding:15px; border-radius:8px; text-align:left; overflow-y:auto; white-space:pre-wrap; font-size:13px; border:1px solid #333; margin:0; font-family:monospace;"></pre>
            </div>

            <script>
                // Submit form silently using AJAX background fetch
                async function startDownload(form) {
                    const btn = form.querySelector('button');
                    btn.disabled = true;
                    btn.style.background = '#444';
                    try {
                        await fetch('/download', { method: 'POST', body: new FormData(form) });
                        alert('Job dispatched to background queue successfully!');
                        form.querySelector('input[name="url"]').value = '';
                        form.querySelector('input[name="audio_url"]').value = '';
                    } catch (e) {
                        alert('Connection error occurred.');
                    } finally {
                        btn.disabled = false;
                        btn.style.background = '#1DB954';
                    }
                }

                // Handle Asynchronous Log updates with Smart Autoscroll locks
                async function updateLogs() {
                    const box = document.getElementById('log-box');
                    try {
                        let res = await fetch('/log-text');
                        let text = await res.text();
                        
                        // Check if user is scrolled near the bottom (with a 40px padding buffer)
                        const isAtBottom = (box.scrollHeight - box.clientHeight) <= (box.scrollTop + 40);
                        
                        if (box.innerText !== text) {
                            box.innerText = text;
                            // Only autoscroll down if the user wasn't actively reviewing history up top
                            if (isAtBottom) {
                                box.scrollTop = box.scrollHeight;
                            }
                        }
                    } catch (e) {}
                }
                setInterval(updateLogs, 3000);
                updateLogs();
            </script>
        </body>
    </html>
    """

@app.post("/download", response_class=HTMLResponse)
async def start_download(url: str = Form(...), audio_url: str = Form(None), background_tasks: BackgroundTasks = None):
    background_tasks.add_task(run_download, url, audio_url)
    return PlainTextResponse("Dispatched")

@app.get("/log-text", response_class=PlainTextResponse)
async def log_text():
    try:
        with open(LOG_PATH, "r") as f:
            return "".join(deque(f, maxlen=100))
    except FileNotFoundError:
        return "No active or recent downloads found."
