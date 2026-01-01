'use client'

import { useState } from 'react'
import Link from 'next/link'
import { AudioWaveform, Github, Menu, X, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ModeToggle } from '@/components/mode-toggle'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function Navbar() {
    const [isMenuOpen, setIsMenuOpen] = useState(false)

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
                        <Link href="/docs" className="hover:text-primary transition-colors">
                            Docs
                        </Link>
                        <Link href="/contribution" className="hover:text-primary transition-colors">
                            Community
                        </Link>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <Link href="https://github.com/nishanth-kj/Text-to-Speech" target="_blank">
                        <Button variant="ghost" size="icon" className="w-9 h-9 opacity-70 hover:opacity-100">
                            <Github className="w-5 h-5" />
                        </Button>
                    </Link>
                    <div className="hidden sm:block">
                        <Link href="/studio">
                            <Button size="sm" className="bg-primary text-primary-foreground hover:opacity-90">
                                Launch Studio
                            </Button>
                        </Link>
                    </div>
                    <ModeToggle />

                    {/* Mobile Menu Toggle */}
                    <Button
                        variant="ghost"
                        size="icon"
                        className="md:hidden"
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                    >
                        {isMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                    </Button>
                </div>
            </div>

            {/* Mobile Menu Overlay */}
            {isMenuOpen && (
                <div className="md:hidden absolute top-16 left-0 w-full bg-background border-b border-border/40 p-4 shadow-2xl animate-in slide-in-from-top-5 fade-in duration-200">
                    <div className="flex flex-col space-y-4">
                        <Link
                            href="/studio"
                            className="flex items-center p-2 rounded-md hover:bg-secondary/50 font-medium"
                            onClick={() => setIsMenuOpen(false)}
                        >
                            Studio
                        </Link>
                        <Link
                            href="/docs"
                            className="flex items-center p-2 rounded-md hover:bg-secondary/50 font-medium"
                            onClick={() => setIsMenuOpen(false)}
                        >
                            Docs
                        </Link>
                        <Link
                            href="/docs"
                            className="flex items-center p-2 rounded-md hover:bg-secondary/50 font-medium"
                            onClick={() => setIsMenuOpen(false)}
                        >
                            Docs
                        </Link>
                        <Link
                            href="/contribution"
                            className="flex items-center p-2 rounded-md hover:bg-secondary/50 font-medium"
                            onClick={() => setIsMenuOpen(false)}
                        >
                            Community
                        </Link>
                        <div className="pt-2 border-t border-border/20">
                            <Link href="/studio" onClick={() => setIsMenuOpen(false)}>
                                <Button className="w-full bg-primary text-primary-foreground">
                                    Launch Studio
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            )}
        </nav>
    )
}
