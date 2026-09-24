import type { Metadata } from "next"
import Link from "next/link"
import { LegalPage } from "@/components/legal-page"
import { GITHUB_URL, RELEASES_URL } from "@/lib/links"
import { LEGAL_EFFECTIVE_DATE } from "@/lib/site"

export const metadata: Metadata = {
  title: "Terms of Service",
  description:
    "Terms for using the VoxLabs website and desktop application, including consent for voice cloning and AI-generated audio labels.",
}

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Service">
      <p className="text-lg">
        Effective {LEGAL_EFFECTIVE_DATE}. By using the VoxLabs website or desktop application, you agree to these terms.
      </p>

      <h2>What VoxLabs is</h2>
      <p>
        VoxLabs is a desktop application for ethical voice cloning and emotional text-to-speech, plus this static website that describes the product and links to{" "}
        <a href={RELEASES_URL} target="_blank" rel="noreferrer">
          downloads
        </a>
        . The product UI is the desktop app, not this website.
      </p>

      <h2>License</h2>
      <p>
        Source code is offered under the MIT License in the{" "}
        <a href={`${GITHUB_URL}/blob/main/LICENSE`} target="_blank" rel="noreferrer">
          repository
        </a>
        . These terms add acceptable-use rules for voice cloning and generated audio. They do not replace the MIT License for the code itself.
      </p>

      <h2>Acceptable use</h2>
      <ul>
        <li>Do not clone a voice without explicit consent from the speaker (or lawful authority to do so).</li>
        <li>Do not use VoxLabs to impersonate someone, commit fraud, harass, or break the law.</li>
        <li>Do not generate illegal, harmful, or rights-violating content.</li>
        <li>Keep generated audio labeled as AI-generated where disclosure is required or reasonably expected.</li>
      </ul>

      <h2>Your content</h2>
      <p>
        You retain rights to text you enter and audio you lawfully own or are licensed to use. You are responsible for having the rights and consents needed to clone a voice and to publish the output.
      </p>

      <h2>AI-generated output</h2>
      <p>
        Synthesized speech is machine-generated. It may be inaccurate or unlike the reference speaker. VoxLabs labels output as AI-generated; you must not strip that label to deceive others.
      </p>

      <h2>No warranty</h2>
      <p>
        The website and software are provided &quot;as is&quot; without warranties of any kind, as described in the MIT License. We do not promise uninterrupted availability of GitHub Pages, Releases, or third-party links.
      </p>

      <h2>Privacy</h2>
      <p>
        Data handling is described in the <Link href="/legal/privacy">privacy policy</Link> and{" "}
        <Link href="/legal/cookies">cookie policy</Link>. Ethics rules are in the{" "}
        <Link href="/legal/ethics">ethical AI guidelines</Link>.
      </p>

      <h2>Changes</h2>
      <p>
        We may update these terms by posting a new version on this page. Continued use after a change means you accept the updated terms.
      </p>
    </LegalPage>
  )
}
