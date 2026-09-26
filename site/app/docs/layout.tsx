import type { ReactNode } from "react"
import { JsonLd } from "@/components/json-ld"
import { breadcrumbJsonLd, pageMetadata } from "@/lib/site"

export const metadata = pageMetadata({
  path: "/docs",
  title: "Docs",
  description:
    "Complete VoxLabs documentation: desktop installation, consent-based voice cloning, offline TTS models, script-to-audio, non-destructive DSP editor, REST API, and MCP server.",
})

export default function DocsLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <JsonLd data={breadcrumbJsonLd([{ name: "Docs", path: "/docs" }])} />
      {children}
    </>
  )
}
