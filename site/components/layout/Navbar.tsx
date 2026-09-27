'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Github, Menu, X, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ModeToggle } from '@/components/mode-toggle'
import { GITHUB_URL, RELEASES_URL } from '@/lib/links'

export function Navbar() {
    const [isMenuOpen, setIsMenuOpen] = useState(false)

    return (
        <nav className="border-b border-white/5 bg-background/50 backdrop-blur-xl sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                <div className="flex items-center gap-8">
                    <Link href="/" className="flex items-center gap-2.5 transition-opacity hover:opacity-80">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="#6352f0"
                            strokeWidth="1.8"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="h-8 w-8 shrink-0 shadow-lg shadow-indigo-500/20 rounded-lg"
                            aria-hidden="true"
                        >
                            <rect x="1" y="1" width="22" height="22" rx="6" fill="#6352f0" stroke="none" />
                            <path d="M7 10v4M10 7v10M13 9v6M16 11v2" stroke="#ffffff" strokeWidth="2.2" />
                        </svg>
                        <span className="font-bold text-lg tracking-tight text-foreground">
                            VoxLabs
                        </span>
                    </Link>

                    <div className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
                        <Link href="/#features" className="hover:text-primary transition-colors">
                            Features
                        </Link>
                        <Link href="/#how-it-works" className="hover:text-primary transition-colors">
                            How it works
                        </Link>
                        <Link href="/#download" className="hover:text-primary transition-colors">
                            Download
                        </Link>
                        <Link href="/docs" className="hover:text-primary transition-colors">
                            Docs
                        </Link>
                        <Link href="/contribution" className="hover:text-primary transition-colors">
                            Contribution
                        </Link>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <Link href={GITHUB_URL} target="_blank">
                        <Button variant="ghost" size="icon" className="w-9 h-9 opacity-70 hover:opacity-100">
                            <Github className="w-5 h-5" />
                        </Button>
                    </Link>
                    <div className="hidden sm:block">
                        <a href={RELEASES_URL}>
                            <Button size="sm" className="bg-primary text-primary-foreground hover:opacity-90">
                                <Download className="w-4 h-4" />
                                Download
                            </Button>
                        </a>
                    </div>
                    <ModeToggle />

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

            {isMenuOpen && (
                <div className="md:hidden absolute top-16 left-0 w-full bg-background border-b border-border/40 p-4 shadow-2xl animate-in slide-in-from-top-5 fade-in duration-200">
                    <div className="flex flex-col space-y-4">
                        <Link
                            href="/#features"
                            className="flex items-center p-2 rounded-md hover:bg-secondary/50 font-medium"
                            onClick={() => setIsMenuOpen(false)}
                        >
                            Features
                        </Link>
                        <Link
                            href="/#how-it-works"
                            className="flex items-center p-2 rounded-md hover:bg-secondary/50 font-medium"
                            onClick={() => setIsMenuOpen(false)}
                        >
                            How it works
                        </Link>
                        <Link
                            href="/#download"
                            className="flex items-center p-2 rounded-md hover:bg-secondary/50 font-medium"
                            onClick={() => setIsMenuOpen(false)}
                        >
                            Download
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
                            Contribution
                        </Link>
                        <div className="pt-2 border-t border-border/20">
                            <a href={RELEASES_URL} onClick={() => setIsMenuOpen(false)}>
                                <Button className="w-full bg-primary text-primary-foreground">
                                    <Download className="w-4 h-4" />
                                    Download
                                </Button>
                            </a>
                        </div>
                    </div>
                </div>
            )}
        </nav>
    )
}
