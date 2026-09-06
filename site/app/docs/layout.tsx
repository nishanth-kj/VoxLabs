import type { Metadata } from "next"
import type { ReactNode } from "react"

export const metadata: Metadata = {
  title: "Docs",
  description:
    "Install the VoxLabs desktop app, clone a voice with consent, generate speech locally, and delete voice data.",
}

export default function DocsLayout({ children }: { children: ReactNode }) {
  return children
}
