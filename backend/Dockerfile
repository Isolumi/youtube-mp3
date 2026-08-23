FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --frozen ensures we use the exact versions in uv.lock
RUN uv sync --frozen --no-dev

# Enforce the minimum yt-dlp release that contains the YouTube download fix.
RUN uv run python -c "import yt_dlp; assert tuple(map(int, yt_dlp.version.__version__.split('.'))) >= (2026, 8, 19), yt_dlp.version.__version__"

# Copy application code
COPY main.py .

# Expose port
EXPOSE 8000

# Run the application using uv
CMD ["uv", "run", "python", "main.py"]
