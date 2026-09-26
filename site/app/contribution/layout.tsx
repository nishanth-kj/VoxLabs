import type { ReactNode } from "react"
import { JsonLd } from "@/components/json-ld"
import { breadcrumbJsonLd, pageMetadata } from "@/lib/site"

export const metadata = pageMetadata({
  path: "/contribution",
  title: "Contribution",
  description:
    "Contribute to VoxLabs. Join GitHub Discussions, share feedback, and help with the open-source desktop voice studio.",
})

export default function ContributionLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <JsonLd data={breadcrumbJsonLd([{ name: "Contribution", path: "/contribution" }])} />
      {children}
    </>
  )
}
