# React + Vite Frontend Design

## Goal

Replace the current client-only Next.js shell with a React + Vite single-page application while preserving the existing download queue, progress polling, filename editing, and MP3 download behavior.

## Design

- Keep the FastAPI backend and its `/download`, `/status/{job_id}`, and `/result/{job_id}` API unchanged.
- Use Vite to build a static React frontend into `frontend/dist`.
- Keep the existing visual design and component behavior, moving the client component into a normal React entry point.
- Read `VITE_API_URL` at build time, defaulting to `http://localhost:8000`.
- Remove Next-only files, dependencies, configuration, and deployment instructions.
- Keep the frontend as one focused component for now; split it only if the refactor requires a clear boundary.

## Success Criteria

- `npm run dev` starts the React UI.
- `npm run build` produces a static `dist` directory.
- The production build can be served by Cloudflare Pages or any static file host.
- The existing UI and backend request flow remain functional.
- No Next.js dependencies or configuration remain.
