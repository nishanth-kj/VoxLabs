import { Button } from "@/components/ui/button"
import { Code2, ArrowRight } from "lucide-react"
import Link from "next/link"

export default function ApiAccessPage() {
    return (
        <div className="min-h-screen bg-background text-foreground pt-32 pb-20 px-6">
            <div className="max-w-4xl mx-auto space-y-12">
                <div className="text-center space-y-6">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 mb-4">
                        <Code2 className="w-8 h-8 text-emerald-500" />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
                        Developer API
                    </h1>
                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                        Integrate VoxLabs' state-of-the-art voice synthesis directly into your applications.
                    </p>
                    <div className="flex justify-center gap-4">
                        <Link href="https://github.com/nishanth-kj/Text-to-Speech" target="_blank">
                            <Button size="lg" className="h-12 px-8">
                                View Documentation
                                <ArrowRight className="ml-2 w-4 h-4" />
                            </Button>
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    )
}
