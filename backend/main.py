import uuid
import os
from pathlib import Path
import shutil
import time
from urllib.parse import urlparse, parse_qs
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
from contextlib import asynccontextmanager


# Cleanup logic: remove files older than 1 hour
def cleanup_old_jobs():
    now = time.time()
    to_delete = []
    
    # We'll use a copy to avoid modification during iteration
    for jid, job in list(jobs.items()):
        # Check if job was created more than 1 hour ago
        if now - job.get("created_at", 0) > 3600:
            to_delete.append(jid)
    
    for jid in to_delete:
        try:
            # Remove directory
            job_dir = Path(f"/tmp/youtube_mp3/{jid}")
            if job_dir.exists():
                shutil.rmtree(job_dir)
            
            # Remove from URL mapping if it's the current one
            url = jobs[jid].get("url")
            if url and url_to_job_id.get(url) == jid:
                del url_to_job_id[url]
            
            # Remove from jobs dict
            del jobs[jid]
            print(f"[{jid}] Cleaned up expired job files")
        except Exception as e:
            print(f"[{jid}] Error during cleanup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: could do something here if needed
    yield
    # Shutdown: could do cleanup here
    cleanup_old_jobs()

app = FastAPI(title="YouTube -> MP3", lifespan=lifespan)

# Get allowed origins from environment variable (comma-separated)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage
jobs: dict[str, dict] = {}
# Map URL to active or completed job_id to prevent redundant downloads
url_to_job_id: dict[str, str] = {}


class DownloadRequest(BaseModel):
    url: str


def process_download(job_id: str, url: str):
    """Background task to download and convert video"""
    print(f"[{job_id}] Starting download for: {url}")
    jobs[job_id]["status"] = "downloading"
    jobs[job_id]["progress"] = 0
    last_reported_progress = -5.0  # Force first progress report

    def progress_hook(d):
        nonlocal last_reported_progress
        if d['status'] == 'downloading':
            try:
                # Calculate progress percentage
                if d.get('total_bytes'):
                    progress = (d.get('downloaded_bytes', 0) / d['total_bytes']) * 100
                elif d.get('total_bytes_estimate'):
                    progress = (d.get('downloaded_bytes', 0) / d['total_bytes_estimate']) * 100
                else:
                    # Fallback to percentage string
                    percent_str = d.get('_percent_str', '0%').strip().replace('%', '')
                    progress = float(percent_str) if percent_str else 0

                jobs[job_id]["progress"] = min(progress, 99)  # Cap at 99% until conversion
                
                # Only log every 10% to reduce verbosity
                if progress >= last_reported_progress + 10:
                    print(f"[{job_id}] Progress: {jobs[job_id]['progress']:.1f}%")
                    last_reported_progress = progress
            except:
                pass
        elif d['status'] == 'finished':
            jobs[job_id]["progress"] = 99
            jobs[job_id]["status"] = "converting"
            print(f"[{job_id}] Download finished, converting to MP3...")

    try:
        download_dir = Path(f"/tmp/youtube_mp3/{job_id}")
        download_dir.mkdir(parents=True, exist_ok=True)
        output_path = download_dir / "%(title)s.%(ext)s"

        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,  # Prevent downloading entire playlists
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": str(output_path),
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_file = Path(filename).with_suffix(".mp3")

            # Extract metadata
            title = info.get("title", "Unknown Title")
            author = info.get("uploader", info.get("channel", "Unknown Author"))

            if not mp3_file.exists():
                # Try to find any mp3 files in the directory
                mp3_files = list(download_dir.glob("*.mp3"))
                if mp3_files:
                    mp3_file = mp3_files[0]
                else:
                    jobs[job_id]["status"] = "error"
                    jobs[job_id]["error"] = "Failed to convert to MP3"
                    print(f"[{job_id}] Error: No MP3 file found in {download_dir}")
                    return

            jobs[job_id]["status"] = "complete"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["file_path"] = str(mp3_file)
            jobs[job_id]["title"] = title
            jobs[job_id]["author"] = author
            print(f"[{job_id}] Complete: {title}")

    except yt_dlp.utils.DownloadError as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = f"Download failed: {str(e)}"
        print(f"[{job_id}] yt-dlp error: {str(e)}")
        # Remove from mapping if it failed so user can try again
        if url in url_to_job_id and url_to_job_id[url] == job_id:
            del url_to_job_id[url]
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = f"An error occurred: {str(e)}"
        print(f"[{job_id}] Unexpected error: {str(e)}")
        if url in url_to_job_id and url_to_job_id[url] == job_id:
            del url_to_job_id[url]


def sanitize_youtube_url(url: str) -> str:
    """
    Extracts the clean video URL, removing playlist/radio parameters.
    Handles watch?v=, shorts/, and youtu.be/ formats.
    """
    try:
        parsed = urlparse(url)
        # Handle youtu.be/VIDEO_ID
        if parsed.netloc == 'youtu.be':
            return f"https://www.youtube.com/watch?v={parsed.path.lstrip('/')}"
        
        # Handle youtube.com/shorts/VIDEO_ID
        if '/shorts/' in parsed.path:
            video_id = parsed.path.split('/shorts/')[1].split('?')[0]
            return f"https://www.youtube.com/watch?v={video_id}"
            
        # Handle youtube.com/watch?v=VIDEO_ID
        if 'watch' in parsed.path:
            query = parse_qs(parsed.query)
            if 'v' in query:
                video_id = query['v'][0]
                return f"https://www.youtube.com/watch?v={video_id}"
        
        # Return original if we can't parse it specifically, 
        # but remove everything except the primary path and 'v' query
        return url
    except Exception:
        return url


@app.post("/download")
async def create_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Submit a download job. Returns existing job_id if already processing.
    """
    # Periodic cleanup on new requests
    background_tasks.add_task(cleanup_old_jobs)
    
    # Sanitize the URL to handle radio/playlist edge cases
    url = sanitize_youtube_url(request.url)
    
    # Check if we already have a job for this URL
    if url in url_to_job_id:
        existing_id = url_to_job_id[url]
        if existing_id in jobs:
            # If it's not an error, reuse it
            if jobs[existing_id]["status"] != "error":
                return {"job_id": existing_id, "status": jobs[existing_id]["status"]}
            else:
                # If the previous one errored, let them try again
                del url_to_job_id[url]

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "url": url,
        "created_at": time.time(),
    }
    url_to_job_id[url] = job_id

    background_tasks.add_task(process_download, job_id, url)

    return {"job_id": job_id, "status": "pending"}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Check the status of a download job.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    response = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
    }

    if job["status"] == "complete":
        response["title"] = job.get("title")
        response["author"] = job.get("author")
    elif job["status"] == "error":
        response["error"] = job.get("error")

    return response


@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """
    Download the completed MP3 file.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Job is not complete. Status: {job['status']}")

    file_path = Path(job["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=f"{job['title']}.mp3",
    )


@app.get("/")
async def root():
    """API information"""
    return {
        "message": "YouTube to MP3 Converter API",
        "endpoints": {
            "submit": "POST /download - Submit job, get job_id",
            "status": "GET /status/{job_id} - Check job status",
            "result": "GET /result/{job_id} - Download MP3 file",
        },
    }


if __name__ == "__main__":
    import uvicorn
    import sys
    print(f"Starting server on Python {sys.version}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
