# Deployment

The application has two simple pieces:

```text
Browser → Cloudflare Pages (React/Vite static files)
       → Cloudflare Tunnel → FastAPI Docker container
```

## Backend

From `backend/`, start the API container:

```bash
ALLOWED_ORIGINS="https://your-frontend.pages.dev" docker compose up -d --build
```

The API listens on `http://localhost:8000`. Check it with:

```bash
curl http://localhost:8000/
docker compose logs -f api
```

The backend needs Docker, FFmpeg (included in the image), and a Cloudflare Tunnel only if it must be reachable outside the local machine.

## Cloudflare Tunnel

Create a tunnel once, then point its hostname at the local API:

```bash
cloudflared tunnel login
cloudflared tunnel create youtube-mp3-api
cloudflared tunnel route dns youtube-mp3-api api.yourdomain.com
```

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL-ID>
credentials-file: /Users/isolumi/.cloudflared/<TUNNEL-ID>.json

ingress:
  - hostname: api.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

Run it with:

```bash
cloudflared tunnel run youtube-mp3-api
```

## Frontend

From `frontend/`, build the static site with the public API URL:

```bash
VITE_API_URL=https://api.yourdomain.com bun install
VITE_API_URL=https://api.yourdomain.com bun run build
```

Deploy `frontend/dist/` to Cloudflare Pages. For a Git-connected Pages project, use:

- Build command: `bun run build`
- Build directory: `frontend`
- Output directory: `dist`
- Environment variable: `VITE_API_URL=https://api.yourdomain.com`

## Updating

```bash
cd backend
docker compose up -d --build

cd ../frontend
bun install
VITE_API_URL=https://api.yourdomain.com bun run build
```
