import type { Metadata } from "next"
import Link from "next/link"
import { ShieldCheck } from "lucide-react"
import { LegalPage } from "@/components/legal-page"

export const metadata: Metadata = {
  title: "Ethical AI Guidelines",
  description:
    "VoxLabs requires consent for voice cloning, local-first processing, AI-generated labels, and simple deletion of voice data.",
}

export default function EthicsPage() {
  return (
    <LegalPage
      title="Ethical AI Guidelines"
      icon={<ShieldCheck className="w-10 h-10 text-emerald-500" />}
    >
      <p className="text-lg">
        VoxLabs is built for responsible voice AI. These rules apply to the desktop app and to how you use generated audio.
      </p>

      <h2>Consent</h2>
      <p>
        Voice cloning requires explicit consent. Clone only your own voice, or a voice you have documented permission to use. Do not bypass consent capture in the app.
      </p>

      <h2>Local-first processing</h2>
      <p>
        Processing stays on your machine. Do not configure the software to silently upload user audio or voice data to external services. See the{" "}
        <Link href="/legal/privacy">privacy policy</Link>.
      </p>

      <h2>Transparency</h2>
      <p>
        Generated audio must remain labeled as AI-generated. Disclose synthetic speech when it could reasonably deceive a listener.
      </p>

      <h2>Deletion</h2>
      <p>
        Voice data deletion must stay simple and complete. Remove a voice in the app when the speaker revokes consent or you no longer need the project.
      </p>

      <h2>Safety</h2>
      <p>
        Do not use VoxLabs for hate, harassment, scams, non-consensual intimate media, or other harmful impersonation. Report abuse through GitHub Issues.
      </p>
    </LegalPage>
  )
}
