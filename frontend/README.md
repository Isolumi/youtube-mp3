# YouTube to MP3 frontend

This is a React + Vite single-page application. It calls the FastAPI backend directly and builds to static files.

## Local development

From this directory:

```bash
bun install
bun run dev
```

The UI is available at `http://localhost:5173` and uses `http://localhost:8000` by default.

To use another backend:

```bash
VITE_API_URL=https://api.example.com bun run dev
```

## Production build

```bash
bun run build
```

Upload the generated `dist/` directory to Cloudflare Pages or another static host. Set `VITE_API_URL` to the public backend URL before building.

For Kubernetes, `frontend/Dockerfile` packages the build with Nginx. The container serves the UI and proxies `/api` to the in-cluster `yootoob-mp3-api` Service, so the browser only needs one public hostname.
