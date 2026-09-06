# Site Documentation

The VoxLabs **site** is a marketing landing page. The product itself is the **desktop application** (`desktop/`, a Tauri + Next.js app). The website explains the product and links to installers — it is not a web Studio.

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn UI (Radix Primitives)
- **Animations**: GSAP
- **Icons**: Lucide React

## Architecture

### `site/app/page.tsx`

Single landing page with:

1. **Hero** — desktop-first headline and a Download CTA (OS-detected).
2. **Features** — emotional TTS, consent-based cloning, local processing.
3. **How it works** — download → consent & clone → synthesize → stay local.
4. **Download** — Windows, macOS, and Linux cards pointing at GitHub Releases.

### Other routes

- `/docs` — install and usage for the desktop app
- `/contribution` — contribute page, with GitHub Discussions as the community CTA (`/discussions` redirects here)
- `/legal/privacy`, `/legal/terms`, `/legal/ethics` — product guarantees

There is no in-browser Studio, library, or TTS workspace on this site.

### GitHub Pages

`site/next.config.ts` uses `output: "export"` so the build writes a static `site/out/` directory. GitHub Pages has no Node server, so redirects in `next.config` are not used. `/discussions/` is a static HTML redirect to `/contribution/`.

Set `NEXT_PUBLIC_BASE_PATH` when the site is not at the domain root (the deploy workflow sets this from Pages). Leave it empty for local `npm run dev`.

### Links (`site/lib/links.ts`)

Release and GitHub URLs are centralized. Download buttons should keep pointing at GitHub Releases rather than hosting binaries in the Next.js app.
