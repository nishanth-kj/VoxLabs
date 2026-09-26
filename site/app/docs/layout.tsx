import type { ReactNode } from "react"
import { JsonLd } from "@/components/json-ld"
import { breadcrumbJsonLd, pageMetadata } from "@/lib/site"

export const metadata = pageMetadata({
  path: "/docs",
  title: "Docs",
  description:
    "Install the VoxLabs desktop app, clone a voice with consent, generate speech locally, and delete voice data.",
})

export default function DocsLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <JsonLd data={breadcrumbJsonLd([{ name: "Docs", path: "/docs" }])} />
      {children}
    </>
  )
}
