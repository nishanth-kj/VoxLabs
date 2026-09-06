'use client'

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Github, MessageSquare, Code2, Users } from "lucide-react"
import Link from "next/link"
import { DISCUSSIONS_URL, GITHUB_URL } from "@/lib/links"

export default function ContributionPage() {
    return (
        <div className="min-h-screen bg-background text-foreground pt-12 pb-20 px-6">
            <div className="max-w-4xl mx-auto space-y-12">

                <div className="text-center space-y-4">
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
                        Contribution
                    </h1>
                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                        Help build VoxLabs. Talk with the community on GitHub Discussions, then jump into the repo when you are ready to contribute.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card className="bg-card/50 border-border/40">
                        <CardContent className="pt-6 text-center space-y-4">
                            <div className="mx-auto w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                                <MessageSquare className="w-6 h-6 text-indigo-400" />
                            </div>
                            <h3 className="font-semibold text-lg">Discussions</h3>
                            <p className="text-sm text-muted-foreground">
                                Ask questions, share builds, and get help with the desktop app on GitHub Discussions.
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-card/50 border-border/40">
                        <CardContent className="pt-6 text-center space-y-4">
                            <div className="mx-auto w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                                <Users className="w-6 h-6 text-purple-400" />
                            </div>
                            <h3 className="font-semibold text-lg">Share</h3>
                            <p className="text-sm text-muted-foreground">
                                Post ideas, feedback, and how you use ethical voice cloning.
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-card/50 border-border/40">
                        <CardContent className="pt-6 text-center space-y-4">
                            <div className="mx-auto w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                                <Code2 className="w-6 h-6 text-foreground" />
                            </div>
                            <h3 className="font-semibold text-lg">Code</h3>
                            <p className="text-sm text-muted-foreground">
                                Fix bugs, add features, or improve docs in the GitHub repository.
                            </p>
                        </CardContent>
                    </Card>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
                    <Link href={DISCUSSIONS_URL} target="_blank">
                        <Button size="lg" className="h-12 px-8 gap-2">
                            <MessageSquare className="w-5 h-5" />
                            Open GitHub Discussions
                        </Button>
                    </Link>
                    <Link href={GITHUB_URL} target="_blank">
                        <Button size="lg" variant="outline" className="h-12 px-8 gap-2">
                            <Github className="w-5 h-5" />
                            View repository
                        </Button>
                    </Link>
                </div>

            </div>
        </div>
    )
}
