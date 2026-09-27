import type { MetadataRoute } from "next"
import { SITE_DESCRIPTION, SITE_NAME, SITE_TAGLINE, getBasePath } from "@/lib/site"

export const dynamic = "force-static"

export default function manifest(): MetadataRoute.Manifest {
  const basePath = getBasePath()
  return {
    name: `${SITE_NAME} — ${SITE_TAGLINE}`,
    short_name: SITE_NAME,
    description: SITE_DESCRIPTION,
    start_url: `${basePath}/`,
    display: "browser",
    background_color: "#0a0c14",
    theme_color: "#0a0c14",
    lang: "en",
    icons: [
      { src: `${basePath}/icon.svg`, sizes: "any", type: "image/svg+xml" },
      { src: `${basePath}/icon-192.png`, sizes: "192x192", type: "image/png" },
      { src: `${basePath}/icon-512.png`, sizes: "512x512", type: "image/png" },
    ],
  }
}
