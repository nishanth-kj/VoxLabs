import type { Metadata } from "next"
import type { ReactNode } from "react"

export const metadata: Metadata = {
  title: "Contribution",
  description:
    "Contribute to VoxLabs. Join GitHub Discussions, share feedback, and help with the open-source desktop voice studio.",
}

export default function ContributionLayout({ children }: { children: ReactNode }) {
  return children
}
