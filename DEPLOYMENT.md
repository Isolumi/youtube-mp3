# Production Deployment Guide

This guide will help you deploy your YouTube MP3 converter with:
- Backend running in Docker on your local machine
- Cloudflare Tunnel exposing the backend to the internet
- Frontend deployed to Cloudflare Pages
- Secure access via your domain name

## Prerequisites

- [x] cloudflared installed (already done)
- [ ] Cloudflare account with your domain added
- [ ] Docker and Docker Compose installed
- [ ] Git repository for your frontend

## Step 1: Set Up Cloudflare Tunnel

### 1.1 Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This will open a browser window. Log in to your Cloudflare account and select the domain you want to use.

### 1.2 Create a Tunnel

```bash
cloudflared tunnel create youtube-mp3-api
```

This creates a tunnel and saves credentials to `~/.cloudflared/<TUNNEL-ID>.json`. Note the tunnel ID that's displayed.

### 1.3 Create Tunnel Configuration

Create a config file at `~/.cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL-ID>  # Replace with your tunnel ID from step 1.2
credentials-file: /Users/isolumi/.cloudflared/<TUNNEL-ID>.json

ingress:
  # Route your API subdomain to the local backend
  - hostname: api.yourdomain.com  # Replace with your domain
    service: http://localhost:8000
  # Catch-all rule (required)
  - service: http_status:404
```

### 1.4 Create DNS Record

```bash
cloudflared tunnel route dns youtube-mp3-api api.yourdomain.com
```

Replace `api.yourdomain.com` with your actual subdomain.

### 1.5 Run the Tunnel

Test the tunnel:

```bash
cloudflared tunnel run youtube-mp3-api
```

Keep this running in a terminal. If it works, you can set it up as a service (see Step 5).

## Step 2: Start Your Backend with Docker

Navigate to your backend directory and start the Docker container:

```bash
cd /Users/isolumi/Documents/CS/youtube-mp3/backend
```

Set the allowed origins environment variable and start the container:

```bash
ALLOWED_ORIGINS="http://localhost:3000,https://yourdomain.com,https://www.yourdomain.com" docker-compose up -d
```

Replace `yourdomain.com` with your actual domain.

**Important**: Add all domains that will access your API, including:
- `http://localhost:3000` (for local development)
- Your Cloudflare Pages URL (e.g., `https://your-app.pages.dev`)
- Your custom domain (e.g., `https://yourdomain.com`)

Verify the container is running:

```bash
docker-compose ps
docker-compose logs -f
```

## Step 3: Test the Tunnel

Test that your API is accessible via the tunnel:

```bash
curl https://api.yourdomain.com
```

You should see:

```json
{
  "message": "YouTube to MP3 Converter API",
  "endpoints": {
    "submit": "POST /download - Submit job, get job_id",
    "status": "GET /status/{job_id} - Check job status",
    "result": "GET /result/{job_id} - Download MP3 file"
  }
}
```

## Step 4: Deploy Frontend to Cloudflare Pages

### 4.1 Update Frontend Environment Variables

Create `.env.production` in your Next.js project:

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

Replace with your actual API subdomain.

### 4.2 Update Frontend Code

Your frontend should already use `process.env.NEXT_PUBLIC_API_URL`. If not, update it:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Example usage:
fetch(`${API_URL}/download`, { ... })
```

### 4.3 Deploy to Cloudflare Pages

**Option A: Connect Git Repository**

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to **Workers & Pages** > **Create application** > **Pages** > **Connect to Git**
3. Select your repository
4. Configure build settings:
   - **Build command**: `npm run build`
   - **Build output directory**: `.next`
   - **Framework preset**: Next.js (Static HTML Export)
5. Add environment variable:
   - **Variable name**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://api.yourdomain.com`
6. Click **Save and Deploy**

**Option B: Manual Deployment via CLI**

Install Wrangler:

```bash
npm install -g wrangler
```

Authenticate:

```bash
wrangler login
```

Build and deploy:

```bash
cd /Users/isolumi/Documents/CS/youtube-mp3-nextjs
npm run build
wrangler pages deploy .next --project-name=youtube-mp3
```

### 4.4 Set Up Custom Domain (Optional)

In Cloudflare Pages settings:
1. Go to **Custom domains**
2. Add your domain (e.g., `yourdomain.com`)
3. Cloudflare will automatically configure DNS

## Step 5: Make Tunnel Persistent (Run as Service)

To keep the tunnel running permanently:

### On macOS (using Homebrew):

```bash
brew services start cloudflared
```

Or manually configure as a launch agent:

```bash
sudo cloudflared service install
```

### Verify Service is Running:

```bash
brew services list | grep cloudflared
# or
sudo launchctl list | grep cloudflared
```

## Step 6: Update Backend CORS (If Needed)

If you need to add more domains later, update the backend container:

```bash
cd /Users/isolumi/Documents/CS/youtube-mp3/backend

# Stop the container
docker-compose down

# Restart with updated origins
ALLOWED_ORIGINS="http://localhost:3000,https://yourdomain.com,https://your-app.pages.dev" docker-compose up -d
```

## Testing the Full Stack

1. **Test backend locally**:
   ```bash
   curl http://localhost:8000
   ```

2. **Test backend via tunnel**:
   ```bash
   curl https://api.yourdomain.com
   ```

3. **Test frontend locally** (pointing to production API):
   ```bash
   cd /Users/isolumi/Documents/CS/youtube-mp3-nextjs
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com npm run dev
   ```
   Visit `http://localhost:3000` and try downloading a YouTube video.

4. **Test production frontend**:
   Visit your Cloudflare Pages URL or custom domain.

## Troubleshooting

### CORS Issues

If you get CORS errors in the browser console:

1. Check backend logs:
   ```bash
   docker-compose logs -f
   ```

2. Verify `ALLOWED_ORIGINS` includes your frontend domain:
   ```bash
   docker-compose exec api printenv ALLOWED_ORIGINS
   ```

3. Update and restart:
   ```bash
   docker-compose down
   ALLOWED_ORIGINS="http://localhost:3000,https://yourdomain.com" docker-compose up -d
   ```

### Tunnel Not Working

1. Check tunnel status:
   ```bash
   cloudflared tunnel info youtube-mp3-api
   ```

2. Check tunnel logs:
   ```bash
   cloudflared tunnel run youtube-mp3-api
   ```

3. Verify DNS record:
   ```bash
   dig api.yourdomain.com
   ```

### Backend Not Responding

1. Check if container is running:
   ```bash
   docker-compose ps
   ```

2. Check container logs:
   ```bash
   docker-compose logs -f
   ```

3. Test locally first:
   ```bash
   curl http://localhost:8000
   ```

## Maintenance

### Updating Backend Code

```bash
cd /Users/isolumi/Documents/CS/youtube-mp3/backend
git pull  # if using git
docker-compose down
docker-compose build
ALLOWED_ORIGINS="..." docker-compose up -d
```

### Updating Frontend

Push to your git repository, and Cloudflare Pages will auto-deploy. Or use Wrangler:

```bash
cd /Users/isolumi/Documents/CS/youtube-mp3-nextjs
git pull
npm run build
wrangler pages deploy .next --project-name=youtube-mp3
```

### Restarting Services

```bash
# Restart backend
cd /Users/isolumi/Documents/CS/youtube-mp3/backend
docker-compose restart

# Restart tunnel (if running as service)
brew services restart cloudflared
```

## Summary

Your architecture:

```
User Browser
    ↓
[Cloudflare Pages - Frontend]
    ↓ (HTTPS)
[Cloudflare Tunnel - api.yourdomain.com]
    ↓ (HTTP - localhost:8000)
[Docker Container - FastAPI Backend]
    ↓
[yt-dlp + FFmpeg]
```

All traffic is encrypted in transit via Cloudflare's network. Your local machine only accepts connections from the Cloudflare Tunnel, not directly from the internet.
