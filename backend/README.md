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

## Cloudflare Tunnel Setup (Optional)

To expose your backend securely without opening ports, you can use Cloudflare Tunnel:

1. Create a tunnel in the [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/).
2. Choose "Docker" as the environment.
3. Copy the **Tunnel Token**.
4. Create a `.env` file in the `backend/` directory:
   ```env
   TUNNEL_TOKEN=your_token_here
   ALLOWED_ORIGINS=https://your-frontend-domain.com
   ```
5. In your Cloudflare Tunnel configuration on the dashboard, add a Public Hostname:
   - **Service:** `http://api:8000` (within the Docker network)
   - **Hostname:** `api.yourdomain.com`

6. Restart with the tunnel:
   ```bash
   docker compose up -d
   ```

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
