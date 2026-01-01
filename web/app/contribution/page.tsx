'use client'

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Github, Heart, Code2, Users } from "lucide-react"
import Link from "next/link"

export default function ContributionPage() {
    return (
        <div className="min-h-screen bg-background text-foreground pt-32 pb-20 px-6">
            <div className="max-w-4xl mx-auto space-y-12">

                <div className="text-center space-y-4">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary text-xs font-medium text-primary mb-4 border border-border/50">
                        <Heart className="w-3 h-3 text-red-500 fill-current" />
                        <span>Open Source</span>
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
                        Contribute to VoxLabs
                    </h1>
                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                        We're building the future of ethical voice AI together. <br />
                        Whether you're a developer, designer, or researcher, your help fits right in.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card className="bg-card/50 border-border/40">
                        <CardContent className="pt-6 text-center space-y-4">
                            <div className="mx-auto w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                                <Code2 className="w-6 h-6 text-indigo-400" />
                            </div>
                            <h3 className="font-semibold text-lg">Codebase</h3>
                            <p className="text-sm text-muted-foreground">
                                Fix bugs, add features, or improve documentation on our GitHub repository.
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-card/50 border-border/40">
                        <CardContent className="pt-6 text-center space-y-4">
                            <div className="mx-auto w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                                <Users className="w-6 h-6 text-purple-400" />
                            </div>
                            <h3 className="font-semibold text-lg">Community</h3>
                            <p className="text-sm text-muted-foreground">
                                Join discussions, share your voice clones, and help others in our community.
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-card/50 border-border/40">
                        <CardContent className="pt-6 text-center space-y-4">
                            <div className="mx-auto w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                                <Github className="w-6 h-6 text-foreground" />
                            </div>
                            <h3 className="font-semibold text-lg">repository</h3>
                            <p className="text-sm text-muted-foreground">
                                Star us on GitHub and fork the project to start contributing today.
                            </p>
                        </CardContent>
                    </Card>
                </div>

                <div className="text-center pt-8">
                    <Link href="https://github.com/nishanth-kj/Text-to-Speech" target="_blank">
                        <Button size="lg" className="h-12 px-8 gap-2">
                            <Github className="w-5 h-5" />
                            View on GitHub
                        </Button>
                    </Link>
                </div>

            </div>
        </div>
    )
}
