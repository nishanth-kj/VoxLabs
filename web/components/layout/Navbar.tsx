'use client'

import Link from 'next/link'
import { AudioWaveform, Github } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ModeToggle } from '@/components/mode-toggle'

export function Navbar() {
    return (
        <nav className="border-b border-white/5 bg-background/50 backdrop-blur-xl sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                <div className="flex items-center gap-8">
                    <Link href="/" className="flex items-center gap-2 transition-opacity hover:opacity-80">
                        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
                            <AudioWaveform className="h-5 w-5 text-white" />
                        </div>
                        <span className="font-bold text-lg tracking-tight text-foreground">
                            VoxLabs
                        </span>
                    </Link>

                    <div className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
                        <Link href="/studio" className="hover:text-primary transition-colors">
                            Studio
                        </Link>
                        <Link href="/#features" className="hover:text-primary transition-colors">
                            Features
                        </Link>

                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <Link href="https://github.com/nishanth-kj/Text-to-Speech" target="_blank">
                        <Button variant="ghost" size="icon" className="w-9 h-9 opacity-70 hover:opacity-100">
                            <Github className="w-5 h-5" />
                        </Button>
                    </Link>
                    <Link href="/studio">
                        <Button size="sm" className="bg-primary text-primary-foreground hover:opacity-90">
                            Launch Studio
                        </Button>
                    </Link>
                    <ModeToggle />
                </div>
            </div>
        </nav>
    )
}
