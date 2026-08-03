# React + Vite Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the unused Next.js runtime with a small React + Vite static frontend while preserving the current downloader behavior and appearance.

**Architecture:** Vite builds a React entry point into static files. The browser calls the existing FastAPI backend directly using `VITE_API_URL`; no frontend server runtime or API proxy is needed.

**Tech Stack:** React 19, Vite, TypeScript, Tailwind CSS 4, FastAPI backend.

## Global Constraints

- Keep the backend API contract unchanged.
- Default `VITE_API_URL` to `http://localhost:8000`.
- Preserve the current queue, polling, error, rename, and download interactions.
- Do not add routing, SSR, a database, authentication, or new runtime services.

---

### Task 1: Add the Vite React shell

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Move/adapt: `frontend/src/app/components/YouTubeDownloader.tsx` to `frontend/src/YouTubeDownloader.tsx`
- Move/adapt: `frontend/src/app/globals.css` to `frontend/src/index.css`

**Interfaces:**
- `src/main.tsx` mounts `<App />` into `#root`.
- `App.tsx` renders `YouTubeDownloader`.
- The downloader reads `import.meta.env.VITE_API_URL`.

- [ ] Add Vite scripts and dependencies, plus the React Vite configuration.
- [ ] Add the Vite HTML entry point and React mount entry.
- [ ] Move the existing UI into the Vite source tree and replace the Next environment access.
- [ ] Run the frontend build and confirm it fails only for any migration issues.

### Task 2: Remove Next-specific files and update documentation

**Files:**
- Delete: `frontend/next.config.ts`
- Delete: `frontend/next-env.d.ts`
- Delete: `frontend/src/app/layout.tsx`
- Delete: `frontend/src/app/page.tsx`
- Delete: `frontend/src/app/globals.css`
- Delete: `frontend/src/app/components/YouTubeDownloader.tsx`
- Modify: `frontend/tsconfig.json`
- Modify: `frontend/README.md`
- Modify: `README.md`

**Interfaces:**
- The frontend build output is `frontend/dist`.
- Cloudflare Pages serves `frontend/dist`.

- [ ] Remove unused Next files and dependencies.
- [ ] Update TypeScript and documentation for Vite commands and `VITE_API_URL`.
- [ ] Remove the obsolete host-based/static-export mismatch from deployment instructions.

### Task 3: Verify the migrated application

**Files:**
- Test: `frontend` build and lint commands.

- [ ] Install/sync frontend dependencies with Bun.
- [ ] Run `bun run lint`.
- [ ] Run `bun run build`.
- [ ] Confirm `git diff --check` is clean and the backend remains syntactically valid.
