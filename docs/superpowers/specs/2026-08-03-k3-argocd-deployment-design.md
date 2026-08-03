# k3 + Argo CD Deployment Design

## Goal

Make the application straightforward to build, publish to GHCR, and deploy to the k3 cluster through Argo CD.

## Design

- Build two images: a FastAPI/FFmpeg API image and an Nginx-served React/Vite frontend image.
- The frontend calls `/api`; Nginx proxies that path to the in-cluster API Service. Production therefore uses one public hostname and does not depend on browser CORS.
- Store Kubernetes resources in `k8s/base` and a `k8s/overlays/dumachine` overlay using Kustomize.
- Include an Argo CD `Application` pointing at the overlay.
- GitHub Actions builds and pushes immutable SHA tags to GHCR, then updates the overlay tags so Argo CD can sync the new images.
- Keep job files ephemeral in the API pod; this remains a personal-use deployment with one API replica.

## Success Criteria

- `docker build` succeeds for both images.
- `kubectl apply -k k8s/overlays/dumachine` produces valid resources.
- Argo CD can sync the committed overlay after the hostname and repository settings are changed.
- A browser can use the frontend through one Ingress hostname and reach the API through `/api`.
