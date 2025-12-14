# YouTube to MP3 Converter API

A simple FastAPI application that downloads YouTube videos and converts them to MP3 format.

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
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Quick Start with Docker (Recommended)

The easiest way to run this application is using Docker Compose, which includes all dependencies:

```bash
docker-compose up
```

The API will be available at `http://localhost:8000`

To run in detached mode:
```bash
docker-compose up -d
```

To stop the service:
```bash
docker-compose down
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

## Installation (Local Development)

1. Install dependencies:
```bash
pip install -e .
```

## Usage (Local Development)

1. Start the server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload
```

2. The API will be available at `http://localhost:8000`

## CORS Configuration

The API is pre-configured to allow requests from `http://localhost:3000` (Next.js default port).

To add additional origins, update `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://yourdomain.com"  # Add your production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## API Endpoint

### GET /download

Download YouTube video and convert to MP3. Returns the MP3 file when complete.

**Query Parameters:**
- `url` (required): YouTube video URL

**Example using curl:**
```bash
curl "http://localhost:8000/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --output audio.mp3
```

**Next.js Integration Example:**

```typescript
const handleDownload = (youtubeUrl: string) => {
  const encodedUrl = encodeURIComponent(youtubeUrl);
  window.location.href = `http://localhost:8000/download?url=${encodedUrl}`;
};
```

**Response:**
Returns the MP3 file with proper headers for browser download.

### GET /

Returns API information.

## Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
