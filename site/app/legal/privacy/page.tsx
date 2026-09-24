import type { Metadata } from "next"
import Link from "next/link"
import { LegalPage } from "@/components/legal-page"
import { DISCUSSIONS_URL, GITHUB_URL, ISSUES_URL } from "@/lib/links"
import { LEGAL_EFFECTIVE_DATE, PRIVACY_EMAIL } from "@/lib/site"

export const metadata: Metadata = {
  title: "Privacy Policy",
  description:
    "How VoxLabs handles data on this website and in the desktop app. Voice processing stays local. No silent uploads.",
}

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy">
      <p className="text-lg">
        Effective {LEGAL_EFFECTIVE_DATE}. This policy covers the VoxLabs marketing website and the VoxLabs desktop application.
      </p>

      <h2>Summary</h2>
      <ul>
        <li>The desktop app processes voice and text on your computer by default.</li>
        <li>We do not silently upload voice samples to third-party services.</li>
        <li>This website does not use advertising or analytics cookies.</li>
        <li>You can delete local voice data from the app at any time.</li>
      </ul>

      <h2>Who we are</h2>
      <p>
        VoxLabs is an open-source desktop voice cloning and text-to-speech project. The public website is a static landing page hosted on GitHub Pages. Source code is published at{" "}
        <a href={GITHUB_URL} target="_blank" rel="noreferrer">
          GitHub
        </a>
        .
      </p>

      <h2>This website</h2>
      <p>
        The site is static HTML, CSS, and JavaScript. It exists to explain the product and link to desktop downloads, documentation, and GitHub.
      </p>
      <h3>What we collect</h3>
      <p>
        We do not run a first-party analytics product, account system, or form backend on this site. We do not sell personal data.
      </p>
      <h3>What your browser stores</h3>
      <ul>
        <li>
          <strong>Theme preference</strong> in <code>localStorage</code> (light, dark, or system) so the site remembers your choice.
        </li>
        <li>
          <strong>Cookie notice dismissal</strong> in <code>localStorage</code> so the banner does not keep returning.
        </li>
      </ul>
      <p>
        Details are in the <Link href="/legal/cookies">cookie policy</Link>.
      </p>
      <h3>Hosting and outbound links</h3>
      <p>
        GitHub Pages may process request logs (such as IP address and user agent) under GitHub&apos;s own privacy policy. Links to GitHub Releases, Issues, and Discussions send you to github.com, which is a separate service.
      </p>

      <h2>The desktop application</h2>
      <h3>Voice and text data</h3>
      <p>
        Audio you record or import for cloning, and text you type for synthesis, are processed on your machine. Voice projects are stored locally. We do not use your voice data to train a global model unless you later opt in through an explicit, documented mechanism.
      </p>
      <h3>Consent</h3>
      <p>
        Cloning requires explicit consent. You may only clone your own voice or a voice you have permission to use. See the{" "}
        <Link href="/legal/ethics">ethical AI guidelines</Link>.
      </p>
      <h3>Deletion</h3>
      <p>
        Remove a voice from the app to delete that project data from this computer. Uninstalling the app removes local application data according to your OS.
      </p>
      <h3>Generated audio</h3>
      <p>Exported speech is labeled as AI-generated. You are responsible for how you share it.</p>

      <h2>Children</h2>
      <p>
        VoxLabs is not directed at children under 13. Do not submit a child&apos;s voice without lawful parental consent and a legitimate purpose.
      </p>

      <h2>Your choices</h2>
      <ul>
        <li>Clear site data in your browser to remove theme and notice storage.</li>
        <li>Do not download the app if you do not want local voice processing.</li>
        <li>Delete local voices inside the desktop app.</li>
      </ul>

      <h2>Contact</h2>
      <p>
        Privacy questions: <a href={`mailto:${PRIVACY_EMAIL}`}>{PRIVACY_EMAIL}</a>. You can also open an issue at{" "}
        <a href={ISSUES_URL} target="_blank" rel="noreferrer">
          GitHub Issues
        </a>{" "}
        or start a thread in{" "}
        <a href={DISCUSSIONS_URL} target="_blank" rel="noreferrer">
          Discussions
        </a>
        .
      </p>
    </LegalPage>
  )
}
