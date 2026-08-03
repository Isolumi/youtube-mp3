# k3 + Argo CD Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package and deploy the YouTube MP3 application with GHCR, Kustomize, and Argo CD.

**Architecture:** A React/Vite static image is served by Nginx and proxies `/api` to the FastAPI Service. Kustomize provides reusable resources plus a starmoon overlay, while GitHub Actions publishes SHA-tagged images and updates the overlay tags for Argo CD.

**Tech Stack:** Docker, Nginx, Kubernetes, Kustomize, Argo CD, GitHub Actions, GHCR.

## Global Constraints

- Use one public frontend hostname and `/api` for browser-to-backend traffic.
- Keep one API replica and ephemeral job storage for personal use.
- Use GHCR image names `ghcr.io/isolumi/youtube-mp3-api` and `ghcr.io/isolumi/youtube-mp3-frontend`.
- Require the operator to replace the example Ingress hostname before syncing.

---

### Task 1: Package the frontend for Kubernetes

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/src/app/components/YouTubeDownloader.tsx`

- [ ] Build the frontend with Bun and serve `dist` with Nginx.
- [ ] Make `/api` the production default and proxy `/api` during Vite development.
- [ ] Add Nginx health and API proxy routes.

### Task 2: Add Kustomize resources

**Files:**
- Create: `k8s/base/kustomization.yaml`
- Create: `k8s/base/api-deployment.yaml`
- Create: `k8s/base/api-service.yaml`
- Create: `k8s/base/frontend-deployment.yaml`
- Create: `k8s/base/frontend-service.yaml`
- Create: `k8s/base/ingress.yaml`
- Create: `k8s/overlays/starmoon/kustomization.yaml`
- Create: `k8s/overlays/starmoon/patch-ingress.yaml`

- [ ] Define probes, resource requests/limits, and an explicit ephemeral workspace.
- [ ] Keep the API internal and expose only the frontend through Ingress.
- [ ] Use overlay image tags and a clearly marked example hostname.

### Task 3: Add Argo CD and CI image flow

**Files:**
- Create: `k8s/argocd/application.yaml`
- Create: `.github/workflows/build-images.yml`

- [ ] Publish both images to GHCR on pushes to `development`.
- [ ] Update overlay image tags to the commit SHA and push the GitOps change.
- [ ] Define an Argo CD Application targeting the starmoon overlay.

### Task 4: Document and verify deployment

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `frontend/README.md`

- [ ] Document local image builds, GHCR prerequisites, hostname replacement, and Argo sync.
- [ ] Build both Docker images.
- [ ] Render and validate Kustomize manifests.
- [ ] Run frontend lint/build and backend syntax checks.
