# YouTube to MP3 Converter API

A simple FastAPI application that downloads YouTube videos and converts them to MP3 format using `yt-dlp` and `ffmpeg`.

## Prerequisites

- Python 3.12+
- FFmpeg (required for audio conversion)

### Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
```bash
# Using winget
winget install ffmpeg
```

## Quick Start with Docker (Recommended)

The easiest way to run this application is using Docker Compose, which includes all dependencies:

```bash
docker compose up
```

The API will be available at `http://localhost:8000`

To run in detached mode:
```bash
docker compose up -d
```

To stop the service:
```bash
docker compose down
```

### Alternative: Docker without Compose

1. Build the Docker image:
```bash
docker build -t youtube-mp3 .
```

2. Run the container:
```bash
docker run -p 8000:8000 youtube-mp3
```

## Cloudflare Tunnel (Optional)

Run Cloudflare Tunnel separately on the host and point it at `http://localhost:8000`. See the root [deployment guide](../DEPLOYMENT.md).

## Installation (Local Development)

This project uses `uv` for dependency management.

1. Install [uv](https://github.com/astral-sh/uv)
2. Sync dependencies:
```bash
uv sync
```

## Usage (Local Development)

1. Start the server:
```bash
uv run python main.py
```

Or using uvicorn directly:
```bash
uv run uvicorn main:app --reload
```

2. The API will be available at `http://localhost:8000`

## CORS Configuration

The API is configured to allow requests from `http://localhost:3000` by default. You can change this via the `ALLOWED_ORIGINS` environment variable.

In `docker compose`:
```yaml
environment:
  - ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## API Endpoints

### POST /download

Submit a YouTube video URL for downloading and conversion. Returns a `job_id` immediately.

**Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

**Response:**
```json
{
  "job_id": "uuid-v4-string",
  "status": "pending"
}
```

### GET /status/{job_id}

Check the status and progress of a download job.

**Response:**
```json
{
  "job_id": "uuid-v4-string",
  "status": "downloading",
  "progress": 45.5
}
```

### GET /result/{job_id}

Download the completed MP3 file. Only works when status is `complete`.

### GET /

Returns basic API information.

## Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
