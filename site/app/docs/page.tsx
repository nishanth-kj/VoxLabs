import { Button } from "@/components/ui/button"
import { Download, Monitor, ShieldCheck, Mic, Trash2, Tag } from "lucide-react"
import Link from "next/link"
import { RELEASES_URL } from "@/lib/links"

export default function DocsPage() {
    return (
        <div className="min-h-screen bg-background text-foreground pt-12 pb-20 px-6">
            <div className="max-w-3xl mx-auto space-y-16">
                <div className="space-y-6 border-b border-border/40 pb-12">
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight">Documentation</h1>
                    <p className="text-xl text-muted-foreground leading-relaxed">
                        VoxLabs is a desktop application. This site is only for download and documentation — synthesis happens on your computer.
                    </p>
                    <a href={RELEASES_URL}>
                        <Button>
                            Download the app
                            <Download className="ml-2 w-4 h-4" />
                        </Button>
                    </a>
                </div>

                <section className="space-y-4">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <Monitor className="w-7 h-7 text-indigo-400" />
                        Install
                    </h2>
                    <ol className="list-decimal list-inside space-y-3 text-muted-foreground leading-relaxed">
                        <li>Open the <Link href="/#download" className="text-foreground underline underline-offset-4">download</Link> section and pick Windows, macOS, or Linux.</li>
                        <li>Run the installer (or open the AppImage on Linux).</li>
                        <li>Launch VoxLabs Studio from your applications menu.</li>
                    </ol>
                    <p className="text-sm text-muted-foreground">
                        FFmpeg must be available on your system PATH for audio processing.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <Mic className="w-7 h-7 text-purple-400" />
                        Clone a voice
                    </h2>
                    <p className="text-muted-foreground leading-relaxed">
                        Provide about 30 seconds of clean audio. You may only clone your own voice or a voice you have explicit permission to use. The app will not proceed without consent.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <Tag className="w-7 h-7 text-pink-400" />
                        Generate speech
                    </h2>
                    <p className="text-muted-foreground leading-relaxed">
                        Enter text, choose a cloned or built-in voice, and adjust emotion, speed, pitch, and energy. Exported audio is labeled as AI-generated.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <Trash2 className="w-7 h-7 text-emerald-400" />
                        Delete voice data
                    </h2>
                    <p className="text-muted-foreground leading-relaxed">
                        Voice projects live on disk inside the app data folder. Remove a voice from the project explorer to delete it completely from this machine.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <ShieldCheck className="w-7 h-7 text-emerald-500" />
                        Privacy
                    </h2>
                    <p className="text-muted-foreground leading-relaxed">
                        Processing is local-first. The desktop app does not silently upload voice samples to third-party services. See the{" "}
                        <Link href="/legal/privacy" className="text-foreground underline underline-offset-4">privacy policy</Link>
                        {" "}and{" "}
                        <Link href="/legal/ethics" className="text-foreground underline underline-offset-4">ethical AI guidelines</Link>.
                    </p>
                </section>
            </div>
        </div>
    )
}
