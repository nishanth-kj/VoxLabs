import { Button } from "@/components/ui/button"
import { Download, Monitor, ShieldCheck, Mic, Trash2, Tag, Cpu, Terminal } from "lucide-react"
import Link from "next/link"
import { RELEASES_URL } from "@/lib/links"

export default function DocsPage() {
    return (
        <div className="min-h-screen bg-background text-foreground pt-12 pb-20 px-6">
            <div className="max-w-3xl mx-auto space-y-16">
                <div className="space-y-6 border-b border-border/40 pb-12">
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight">Documentation</h1>
                    <p className="text-xl text-muted-foreground leading-relaxed">
                        VoxLabs is a native desktop application (PySide6). This site is only for download and documentation — synthesis, voice cloning, and audio editing happen on your computer.
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
                        <li>Windows: unzip and run <code>VoxLabs\VoxLabs.exe</code>. macOS: open the .dmg and drag VoxLabs to Applications. Linux: extract the archive and run <code>VoxLabs/VoxLabs</code>.</li>
                        <li>The builds are not code-signed yet, so Windows SmartScreen and macOS Gatekeeper ask you to confirm the first launch.</li>
                    </ol>
                    <p className="text-sm text-muted-foreground">
                        WAV, FLAC, OGG, and MP3 work out of the box via libsndfile. FFmpeg on your system PATH is optional and adds M4A/AAC import and export.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <Cpu className="w-7 h-7 text-cyan-400" />
                        Local AI models
                    </h2>
                    <p className="text-muted-foreground leading-relaxed">
                        Open the <strong>Models</strong> page inside VoxLabs to install local speech engines: <strong>Piper</strong> (63 MB, fast CPU TTS), <strong>Kokoro 82M</strong> (330 MB, expressive CPU/GPU voices like <code>af_heart</code> and <code>af_bella</code>), or full zero-shot voice cloning engines (<strong>Coqui XTTS v2</strong>, <strong>F5-TTS</strong>, and <strong>Chatterbox</strong>). If GPU memory is full, VoxLabs automatically falls back to CPU.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <Mic className="w-7 h-7 text-purple-400" />
                        Clone a voice
                    </h2>
                    <p className="text-muted-foreground leading-relaxed">
                        Provide 3 to 30 seconds of clean speech audio. You may only clone your own voice or a voice you have explicit permission to use. VoxLabs validates audio quality and records attributed speaker consent before cloning.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <Tag className="w-7 h-7 text-pink-400" />
                        Generate speech, scripts &amp; edit audio
                    </h2>
                    <p className="text-muted-foreground leading-relaxed">
                        Enter text or multi-speaker scripts, choose a cloned or built-in voice, and adjust emotion, speed, pitch, energy, and pauses. Refine output in the non-destructive waveform editor with 8-stage DSP enhancement (denoise, EQ, compression, de-esser, limiter, and BS.1770 LUFS loudness). Every generated file is tagged as AI-generated.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <Terminal className="w-7 h-7 text-amber-400" />
                        Optional REST API &amp; MCP server
                    </h2>
                    <p className="text-muted-foreground leading-relaxed">
                        Start the local server from <strong>Settings → REST API</strong> (or run <code>uv run python -m app.api.app</code>) to expose the same services on <code>127.0.0.1:8942</code> alongside a Model Context Protocol (MCP) server at <code>/mcp</code> and over stdio (<code>--stdio</code>).
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <Trash2 className="w-7 h-7 text-emerald-400" />
                        Revoke or delete voice data
                    </h2>
                    <p className="text-muted-foreground leading-relaxed">
                        Voice data lives on disk inside your local <code>data/</code> directory. Revoking consent immediately deletes all reference samples and voice profiles; deleting a voice removes every record from your machine.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <ShieldCheck className="w-7 h-7 text-emerald-500" />
                        Privacy
                    </h2>
                    <p className="text-muted-foreground leading-relaxed">
                        Processing is local-first. The desktop app never uploads voice samples to third-party services. Online TTS engines are disabled unless you explicitly turn them on in Settings. See the{" "}
                        <Link href="/legal/privacy" className="text-foreground underline underline-offset-4">privacy policy</Link>
                        {" "}and{" "}
                        <Link href="/legal/ethics" className="text-foreground underline underline-offset-4">ethical AI guidelines</Link>.
                    </p>
                </section>
            </div>
        </div>
    )
}
