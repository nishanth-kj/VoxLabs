'use client'

import { useRef } from 'react'
import { Button } from "@/components/ui/button"
import { ArrowRight, Download } from "lucide-react"
import Link from 'next/link'
import { gsap } from "gsap"
import { useGSAP } from "@gsap/react"
import { DesktopPreview } from "@/components/landing/desktop-preview"
import { PLATFORMS, RELEASES_URL } from "@/lib/links"
import { usePlatform } from "@/hooks/use-platform"

export function HeroSection() {
    const heroRef = useRef<HTMLDivElement>(null)
    const platform = usePlatform()
    const matched = PLATFORMS.find((p) => p.id === platform) ?? PLATFORMS[0]

    useGSAP(() => {
        gsap.from(heroRef.current, {
            y: 50,
            opacity: 0,
            duration: 1,
            ease: "power3.out",
            delay: 0.2
        })
    }, { scope: heroRef })

    return (
        <section ref={heroRef} className="flex flex-col items-center justify-center pt-10 pb-16 px-6 max-w-7xl mx-auto text-center space-y-6">
            <h1 className="text-4xl sm:text-5xl md:text-7xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 dark:from-white dark:via-white/90 dark:to-white/50 pb-2">
                Your Voice, <br className="hidden md:block" /> Reimagined with AI.
            </h1>

            <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                Clone a voice with consent and generate emotionally resonant speech on your desktop. VoxLabs is a native app — nothing is uploaded to the cloud.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4 w-full sm:w-auto px-6 sm:px-0">
                <a href={matched.href} className="w-full sm:w-auto">
                    <Button size="lg" className="h-12 px-8 text-base shadow-lg shadow-indigo-500/20 w-full sm:w-auto">
                        Download for {matched.label}
                        <Download className="ml-2 w-4 h-4" />
                    </Button>
                </a>
                <Link href="#download" className="w-full sm:w-auto">
                    <Button variant="outline" size="lg" className="h-12 px-8 text-base border-border/40 hover:bg-secondary/50 w-full sm:w-auto">
                        All platforms
                        <ArrowRight className="ml-2 w-4 h-4" />
                    </Button>
                </Link>
            </div>

            <p className="text-xs text-muted-foreground">
                Free to download.{" "}
                <a href={RELEASES_URL} className="underline underline-offset-4 hover:text-foreground">
                    View releases
                </a>
            </p>

            <DesktopPreview />
        </section>
    )
}
