'use client'

import type { ReactNode } from "react"
import { Button } from "@/components/ui/button"
import { Download, Monitor, Laptop, Terminal, ShieldCheck } from "lucide-react"
import { PLATFORMS, RELEASES_URL, type PlatformId } from "@/lib/links"
import { usePlatform } from "@/hooks/use-platform"

const ICONS: Record<PlatformId, ReactNode> = {
    windows: <Monitor className="w-6 h-6" />,
    macos: <Laptop className="w-6 h-6" />,
    linux: <Terminal className="w-6 h-6" />,
}

export function DownloadSection() {
    const platform = usePlatform()

    return (
        <section id="download" className="py-24 px-6 bg-secondary/20 border-t border-border/40">
            <div className="max-w-5xl mx-auto space-y-12">
                <div className="text-center space-y-6">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-500/10 mb-4 border border-indigo-500/20">
                        <Download className="w-8 h-8 text-indigo-400" />
                    </div>
                    <h2 className="text-3xl md:text-5xl font-bold tracking-tight">
                        Download VoxLabs
                    </h2>
                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                        The product is a desktop application. Pick your platform and install — synthesis and cloning run on your computer.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {PLATFORMS.map((item) => {
                        const recommended = platform === item.id
                        return (
                            <a
                                key={item.id}
                                href={item.href}
                                className={`group rounded-xl border bg-card/50 p-6 space-y-4 transition-colors ${
                                    recommended
                                        ? "border-indigo-500/60 shadow-lg shadow-indigo-500/10"
                                        : "border-border/40 hover:border-border/80"
                                }`}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="w-12 h-12 rounded-lg bg-secondary flex items-center justify-center text-indigo-400 group-hover:scale-105 transition-transform">
                                        {ICONS[item.id]}
                                    </div>
                                    {recommended && (
                                        <span className="text-[10px] uppercase tracking-wider font-semibold text-indigo-400">
                                            Your OS
                                        </span>
                                    )}
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold">{item.label}</h3>
                                    <p className="text-sm text-muted-foreground mt-1">{item.requirement}</p>
                                    <p className="text-xs font-mono text-muted-foreground/80 mt-2">{item.fileHint}</p>
                                </div>
                                <Button className="w-full" variant={recommended ? "default" : "outline"}>
                                    Download
                                    <Download className="w-4 h-4" />
                                </Button>
                            </a>
                        )
                    })}
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-3 text-sm text-muted-foreground">
                    <span className="inline-flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        Local-first. No silent uploads of voice data.
                    </span>
                    <span className="hidden sm:inline text-border">·</span>
                    <a href={RELEASES_URL} className="underline underline-offset-4 hover:text-foreground">
                        All releases on GitHub
                    </a>
                </div>
            </div>
        </section>
    )
}
