import Link from 'next/link'
import { GITHUB_URL } from '@/lib/links'

export function Footer() {
    return (
        <footer className="border-t border-white/5 bg-background/50 backdrop-blur-sm mt-auto">
            <div className="max-w-7xl mx-auto px-6 py-12">
                <div className="grid grid-cols-1 md:grid-cols-5 gap-8 mb-12">
                    <div className="md:col-span-2 space-y-4">
                        <Link href="/" className="flex items-center gap-2">
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="#6352f0"
                                strokeWidth="1.8"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className="h-6 w-6 shrink-0 rounded"
                                aria-hidden="true"
                            >
                                <rect x="1" y="1" width="22" height="22" rx="6" fill="#6352f0" stroke="none" />
                                <path d="M7 10v4M10 7v10M13 9v6M16 11v2" stroke="#ffffff" strokeWidth="2.2" />
                            </svg>
                            <span className="font-bold text-base">VoxLabs</span>
                        </Link>
                        <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">
                            Ethical AI voice cloning and emotional speech synthesis — as a desktop app that keeps your voice on your machine.
                        </p>
                    </div>
                    <div>
                        <h4 className="font-semibold text-sm mb-4">Product</h4>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/#features">Features</Link>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/#engines">AI Engines</Link>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/#how-it-works">How it works</Link>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/#faq">FAQ</Link>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/#download">Download</Link>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/docs">Docs</Link>
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="font-semibold text-sm mb-4">Community</h4>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/contribution">Contribution</Link>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href={GITHUB_URL} target="_blank">GitHub</Link>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/llms.txt">llms.txt</Link>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/llms-full.txt">llms-full.txt</Link>
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="font-semibold text-sm mb-4">Legal</h4>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/legal/privacy">Privacy Policy</Link>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/legal/terms">Terms of Service</Link>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/legal/ethics">Ethical AI Guidelines</Link>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <Link href="/legal/cookies">Cookie Policy</Link>
                            </li>
                        </ul>
                    </div>
                </div>
                <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-muted-foreground">
                    <p>&copy; {new Date().getFullYear()} VoxLabs AI. All rights reserved.</p>
                    <p>
                        <Link href="/legal/privacy" className="hover:text-foreground">Privacy</Link>
                        {" · "}
                        <Link href="/legal/cookies" className="hover:text-foreground">Cookies</Link>
                        {" · "}
                        <Link href="/legal/terms" className="hover:text-foreground">Terms</Link>
                    </p>
                </div>
            </div>
        </footer>
    )
}
