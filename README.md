# k3 + Argo CD deployment

The cluster runs two images:

```text
Ingress → yootoob-mp3-frontend (Nginx + React/Vite)
                    │ /api proxy
                    ▼
          yootoob-mp3-api (FastAPI + yt-dlp + FFmpeg)
```

The Kubernetes manifests are in `k8s/`. The `dumachine` overlay is the Argo CD target.

## One-time cluster setup

The images are published to GHCR by GitHub Actions. If the packages are private, create the pull secret in the target namespace:

```bash
kubectl create namespace yootoob-mp3
kubectl -n yootoob-mp3 create secret docker-registry ghcr-pull \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_PAT
```

The PAT needs package read access. If the GHCR packages are public, the secret is not needed; remove the `imagePullSecrets` entries from the two base Deployments.

The dumachine deployment uses `yootoob.dumachine` as its private hostname.

## Argo CD

Apply the Argo Application once:

```bash
kubectl apply -f k8s/argocd/application.yml
```

Argo CD will then track `development`, create the `yootoob-mp3` namespace, and sync `k8s/overlays/dumachine`.

## Image flow

Every push to `development` does the following:

1. Builds and pushes both images to GHCR.
2. Tags them with the commit SHA and `development`.
3. Updates the Kustomize overlay to the commit SHA.
4. Pushes that GitOps commit.
5. Argo CD detects the manifest change and syncs the cluster.

The workflow requires repository Actions permissions to write packages and contents. The checked-in workflow already requests both permissions.

## Local manifest checks

```bash
kubectl kustomize k8s/overlays/dumachine
kubectl apply --dry-run=client -k k8s/overlays/dumachine
```

## Local Docker checks

```bash
docker build -t yootoob-mp3-api:test ./backend
docker build -t yootoob-mp3-frontend:test ./frontend
```

The API stores active jobs and MP3 files in pod-local temporary storage. This is intentional for personal use; restarting the API pod discards its current jobs and files.
