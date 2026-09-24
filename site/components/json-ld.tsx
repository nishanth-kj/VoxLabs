import { SOFTWARE_JSON_LD } from "@/lib/site"

export function JsonLd() {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(SOFTWARE_JSON_LD) }}
    />
  )
}
