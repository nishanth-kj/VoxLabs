# Setup & Deployment Guide

## Prerequisites

- **Python**: 3.12 or higher
- **Node.js**: 20 or higher
- **Rust**: stable toolchain (`rustc`/`cargo`), required to build the desktop app (Tauri) — see [rustup.rs](https://rustup.rs).
- **FFmpeg**: Required for audio processing (must be in system PATH).

## Quick Start (Docker)

The easiest way to run VoxLabs is using Docker Compose.

1.  **Build and Run**:
    ```bash
    docker-compose up --build
    ```
2.  **Access**:
    - Landing site: `http://localhost:3000`
    - API Docs: `http://localhost:8000/docs`

## Local Development

If you prefer to run services manually:

### 1. Backend (API)

```bash
cd api
# Install dependencies (using uv or pip)
uv sync  # or pip install -r requirements.txt

# Run Server
uv run uvicorn main:app --reload --port 8000
```

### 2. Landing site

```bash
cd site
# Install dependencies
npm install

# Run Development Server
npm run dev
```

Visit `http://localhost:3000` for the download landing page. The product UI is the desktop app, not this site.

### GitHub Pages

The landing site is a static Next.js export. On push to `main`, [`.github/workflows/deploy-nextjs.yml`](../.github/workflows/deploy-nextjs.yml) builds `site/` and deploys it.

1. In the GitHub repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Push to `main` (or run the **Deploy Next.js to GitHub Pages** workflow).
3. The site is served at `https://<owner>.github.io/<repo>/` (for this repo, typically `https://nishanth-kj.github.io/VoxLabs/`).

Local production build (no Docker):

```bash
cd site
npm run build
npm run preview
```

### 3. Desktop App (Tauri + Next.js)

```bash
cd desktop
npm install
npm run tauri dev
```

This opens the native window backed by the Next.js frontend (`http://localhost:3000` in dev). It talks to the FastAPI backend, so keep step 1 running alongside it.

## Troubleshooting

- **FFmpeg Error**: If you see errors about "ffmpeg not found", ensure it is installed and added to your system environment variables.
- **API Connection**: Ensure the backend is running on `localhost:8000`. The frontend expects this default URL.
