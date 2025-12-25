import uuid
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="YouTube -> MP3")

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


class DownloadRequest(BaseModel):
    url: str


def process_download(job_id: str, url: str):
    """Background task to download and convert video"""
    print(f"[{job_id}] Starting download for: {url}")
    jobs[job_id]["status"] = "downloading"
    jobs[job_id]["progress"] = 0

    def progress_hook(d):
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
                print(f"[{job_id}] Progress: {jobs[job_id]['progress']:.1f}%")
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
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_file = Path(filename).with_suffix(".mp3")

            # Extract metadata
            title = info.get("title", "Unknown Title")
            author = info.get("uploader", info.get("channel", "Unknown Author"))

            print(f"[{job_id}] Video: {title} by {author}")
            print(f"[{job_id}] Expected MP3 file: {mp3_file}")
            print(f"[{job_id}] Download dir contents: {list(download_dir.glob('*'))}")

            if not mp3_file.exists():
                # Try to find any mp3 files in the directory
                mp3_files = list(download_dir.glob("*.mp3"))
                if mp3_files:
                    mp3_file = mp3_files[0]
                    print(f"[{job_id}] Found MP3 at: {mp3_file}")
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
            print(f"[{job_id}] Complete: {title} by {author}")

    except yt_dlp.utils.DownloadError as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = f"Download failed: {str(e)}"
        print(f"[{job_id}] yt-dlp error: {str(e)}")
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = f"An error occurred: {str(e)}"
        print(f"[{job_id}] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


@app.post("/download")
async def create_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Submit a download job. Returns job_id immediately.
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "url": request.url,
    }

    background_tasks.add_task(process_download, job_id, request.url)

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

    uvicorn.run(app, host="0.0.0.0", port=8000)
