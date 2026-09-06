import { Button } from "@/components/ui/button"
import { Mic, ArrowRight } from "lucide-react"
import Link from "next/link"

export default function VoiceCloningPage() {
    return (
        <div className="min-h-screen bg-background text-foreground pt-32 pb-20 px-6">
            <div className="max-w-4xl mx-auto space-y-12">
                <div className="text-center space-y-6">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-500/10 mb-4">
                        <Mic className="w-8 h-8 text-indigo-500" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
                        Instant Voice Cloning
                    </h1>
                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                        Clone any voice from just 30 seconds of audio. Our advanced model captures tone, accent, and emotional nuance.
                    </p>
                    <div className="flex justify-center gap-4">
                        <Link href="/studio">
                            <Button size="lg" className="h-12 px-8">
                                Try it in Studio
                                <ArrowRight className="ml-2 w-4 h-4" />
                            </Button>
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    )
}
