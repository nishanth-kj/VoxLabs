import type { Metadata } from "next"
import Link from "next/link"
import { LegalPage } from "@/components/legal-page"
import { LEGAL_EFFECTIVE_DATE } from "@/lib/site"

export const metadata: Metadata = {
  title: "Cookie Policy",
  description:
    "VoxLabs does not use tracking or advertising cookies. This page explains browser storage on the landing site.",
}

export default function CookiesPage() {
  return (
    <LegalPage title="Cookie Policy">
      <p className="text-lg">Effective {LEGAL_EFFECTIVE_DATE}.</p>

      <h2>We do not use tracking cookies</h2>
      <p>
        The VoxLabs website does not set advertising, analytics, or social-media tracking cookies. There is no cookie consent wall for optional trackers because those trackers are not present.
      </p>

      <h2>What we store in your browser</h2>
      <p>
        We use <strong>localStorage</strong> (not HTTP cookies) for two essential preferences:
      </p>
      <ul>
        <li>
          <strong>voxlabs-theme</strong> — light, dark, or system appearance. Set when you use the theme toggle.
        </li>
        <li>
          <strong>voxlabs-cookie-notice</strong> — remembers that you dismissed this notice.
        </li>
      </ul>
      <p>
        These are strictly necessary for the site to remember your UI choices. They stay on your device and are not sent to a VoxLabs server (this site has no application backend).
      </p>

      <h2>Third parties</h2>
      <p>
        If you follow a link to GitHub (downloads, source, or discussions), GitHub may set its own cookies under GitHub&apos;s policies. The desktop app does not set website cookies.
      </p>
      <p>
        GitHub Pages, which hosts this site, may process technical request data as described in GitHub&apos;s privacy statement.
      </p>

      <h2>How to clear storage</h2>
      <p>
        Use your browser settings to clear site data for this origin. That removes theme and notice preferences. The notice may appear again on the next visit.
      </p>

      <h2>Related</h2>
      <p>
        See the <Link href="/legal/privacy">privacy policy</Link> for how the desktop app handles voice data.
      </p>
    </LegalPage>
  )
}
