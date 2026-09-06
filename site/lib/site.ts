import { GITHUB_URL, RELEASES_URL } from "@/lib/links"

function normalizeBasePath(value: string | undefined) {
  if (!value || value === "/") return ""
  return value.endsWith("/") ? value.slice(0, -1) : value
}

export const SITE_NAME = "VoxLabs"
export const SITE_TAGLINE = "Download the desktop voice studio"
export const SITE_DESCRIPTION =
  "Ethical AI voice cloning and emotional text-to-speech as a desktop app. Processing stays on your machine. Download for Windows, macOS, and Linux."
export const SITE_KEYWORDS = [
  "VoxLabs",
  "voice cloning",
  "text to speech",
  "TTS",
  "desktop app",
  "local AI",
  "ethical AI",
  "emotional speech",
]

export const LEGAL_EFFECTIVE_DATE = "September 6, 2026"
export const PRIVACY_EMAIL = "privacy@voxlabs.ai"

export function getBasePath() {
  return normalizeBasePath(process.env.NEXT_PUBLIC_BASE_PATH)
}

export function getSiteUrl() {
  const explicit = process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "")
  if (explicit) return explicit
  const basePath = getBasePath()
  return `https://nishanth-kj.github.io${basePath || "/VoxLabs"}`
}

export function absoluteUrl(path = "/") {
  const base = getSiteUrl()
  if (!path || path === "/") return `${base}/`
  const normalized = path.startsWith("/") ? path : `/${path}`
  if (/\.[a-z0-9]+$/i.test(normalized)) {
    return `${base}${normalized}`
  }
  return `${base}${normalized.endsWith("/") ? normalized : `${normalized}/`}`
}

export const SITE_NAV_PATHS = [
  "/",
  "/docs/",
  "/contribution/",
  "/legal/privacy/",
  "/legal/terms/",
  "/legal/ethics/",
  "/legal/cookies/",
] as const

export const SOFTWARE_JSON_LD = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${getSiteUrl()}/#organization`,
      name: SITE_NAME,
      url: getSiteUrl(),
      sameAs: [GITHUB_URL],
      email: PRIVACY_EMAIL,
    },
    {
      "@type": "WebSite",
      "@id": `${getSiteUrl()}/#website`,
      name: SITE_NAME,
      url: getSiteUrl(),
      description: SITE_DESCRIPTION,
      publisher: { "@id": `${getSiteUrl()}/#organization` },
      inLanguage: "en",
    },
    {
      "@type": "SoftwareApplication",
      name: SITE_NAME,
      applicationCategory: "MultimediaApplication",
      operatingSystem: "Windows, macOS, Linux",
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
      },
      description: SITE_DESCRIPTION,
      downloadUrl: RELEASES_URL,
      url: getSiteUrl(),
      license: `${GITHUB_URL}/blob/main/LICENSE`,
    },
  ],
}
