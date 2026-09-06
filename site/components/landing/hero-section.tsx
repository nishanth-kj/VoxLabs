'use client'

import { useRef } from 'react'
import { Button } from "@/components/ui/button"
import { ArrowRight, Sparkles, PlayCircle } from "lucide-react"
import Link from 'next/link'
import { gsap } from "gsap"
import { useGSAP } from "@gsap/react"

export function HeroSection() {
    const heroRef = useRef<HTMLDivElement>(null)

    useGSAP(() => {
        gsap.from(heroRef.current, {
            y: 50,
            opacity: 0,
            duration: 1,
            ease: "power3.out",
            delay: 0.2 // Small delay to let hydration settle
        })
    }, { scope: heroRef })

    return (
        <section ref={heroRef} className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center py-20 px-6 max-w-7xl mx-auto text-center space-y-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary/50 border border-border/50 text-xs font-medium text-primary mb-4 animate-in fade-in zoom-in duration-500 delay-100">
                <Sparkles className="w-3 h-3" />
                <span>New: Emotional Voice Cloning v2.0</span>
            </div>

            <h1 className="text-4xl sm:text-5xl md:text-7xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 dark:from-white dark:via-white/90 dark:to-white/50 pb-2">
                Your Voice, <br className="hidden md:block" /> Reimagined with AI.
            </h1>

            <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                Create lifelike speech, clone any voice in seconds, and generate emotionally resonant audio for your content. The future of synthesis is here.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4 w-full sm:w-auto px-6 sm:px-0">
                <Link href="/studio" className="w-full sm:w-auto">
                    <Button size="lg" className="h-12 px-8 text-base shadow-lg shadow-indigo-500/20 w-full sm:w-auto">
                        Start Creating Free
                        <ArrowRight className="ml-2 w-4 h-4" />
                    </Button>
                </Link>
                <Link href="#demo" className="w-full sm:w-auto">
                    <Button variant="outline" size="lg" className="h-12 px-8 text-base border-border/40 hover:bg-secondary/50 w-full sm:w-auto">
                        Listen to Samples
                        <PlayCircle className="ml-2 w-4 h-4" />
                    </Button>
                </Link>
            </div>
        </section>
    )
}
