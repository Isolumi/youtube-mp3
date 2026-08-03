# `lumilumi.xyz` HTTPS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve `yootoob.dumachine.lumilumi.xyz` over publicly trusted HTTPS while keeping the service private through Tailscale.

**Architecture:** cert-manager will use Let’s Encrypt DNS-01 validation through Cloudflare. Private DNS will resolve the hostname to dumachine’s Tailscale IP, while Cloudflare is used only to prove domain ownership and create temporary ACME TXT records. Traefik will route both the existing `.dumachine` alias and the new `.lumilumi.xyz` hostname to the same app.

**Tech Stack:** K3s, Traefik, cert-manager, Let’s Encrypt, Cloudflare DNS API, Kubernetes Ingress, Argo CD, Tailscale DNS.

## Global Constraints

- Keep the application private; do not create an A/AAAA record pointing to dumachine’s private Tailscale IP.
- Use Cloudflare only for DNS-01 certificate validation.
- Store the Cloudflare API token only in a Kubernetes Secret; never commit it to Git.
- Use a Cloudflare API token restricted to `Zone - DNS - Edit` and `Zone - Zone - Read` for `lumilumi.xyz`.
- Keep Kubernetes manifest files using `.yml` extensions.

---

### Task 1: Install cert-manager

**Files:**
- Create: `k8s/cert-manager/argocd-application.yml`

- [ ] Install the current cert-manager release manifest.
- [ ] Verify the CRDs and cert-manager controller, webhook, and cainjector are ready.
- [ ] Add the cert-manager configuration to Argo CD management.

### Task 2: Configure Cloudflare DNS-01 and Let’s Encrypt

**Files:**
- Create: `k8s/cert-manager/clusterissuer.yml`
- Create: `k8s/cert-manager/kustomization.yml`

- [ ] Create the `cloudflare-api-token-secret` in the `cert-manager` namespace from the user-provided token without writing it to Git.
- [ ] Create a Let’s Encrypt staging ClusterIssuer first for a safe validation test.
- [ ] Create the production ClusterIssuer after staging succeeds.
- [ ] Configure cert-manager DNS self-check to use public resolvers so private split DNS does not interfere with ACME validation.

### Task 3: Issue the application certificate

**Files:**
- Create: `k8s/overlays/dumachine/certificate.yml`
- Modify: `k8s/overlays/dumachine/kustomization.yml`

- [ ] Request a certificate for `yootoob.dumachine.lumilumi.xyz`.
- [ ] Store it as the namespace-local Secret `yootoob-lumilumi-tls`.
- [ ] Verify the certificate reports `READY=True` and contains the exact hostname.

### Task 4: Add the trusted hostname to the Ingress

**Files:**
- Modify: `k8s/overlays/dumachine/patch-ingress.yml`
- Modify: `k8s/overlays/dumachine/kustomization.yml`

- [ ] Add `yootoob.dumachine.lumilumi.xyz` as a second Ingress host.
- [ ] Bind the Let’s Encrypt Secret to that host.
- [ ] Keep `yootoob.dumachine` available as the private-CA/HTTP alias until we decide whether to remove it.
- [ ] Redirect HTTP to HTTPS for the trusted hostname.

### Task 5: Configure private DNS and verify

- [ ] Add `yootoob.dumachine.lumilumi.xyz` to dumachine’s private DNS mapping so it resolves to `100.121.114.49` through Tailscale.
- [ ] Configure Tailscale DNS to route the `dumachine.lumilumi.xyz` suffix to dumachine’s DNS service.
- [ ] Verify `https://yootoob.dumachine.lumilumi.xyz` has a trusted certificate, loads the app, and supports Google OAuth redirect URIs.
- [ ] Verify Argo CD is `Synced` and `Healthy` and no public service record was created.

