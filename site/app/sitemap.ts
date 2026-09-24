import type { MetadataRoute } from "next"
import { SITE_NAV_PATHS, getSiteUrl } from "@/lib/site"

export const dynamic = "force-static"

export default function sitemap(): MetadataRoute.Sitemap {
  const site = getSiteUrl()
  return SITE_NAV_PATHS.map((path) => ({
    url: path === "/" ? `${site}/` : `${site}${path}`,
    lastModified: new Date("2026-09-06"),
    changeFrequency: path === "/" ? "weekly" : "monthly",
    priority: path === "/" ? 1 : 0.7,
  }))
}
