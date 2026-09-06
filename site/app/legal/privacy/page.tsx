export default function PrivacyPage() {
    return (
        <div className="min-h-screen bg-background text-foreground pt-32 pb-20 px-6">
            <div className="max-w-3xl mx-auto space-y-8">
                <h1 className="text-4xl font-bold tracking-tight mb-8">Privacy Policy</h1>

                <div className="prose dark:prose-invert max-w-none">
                    <p className="text-muted-foreground text-lg leading-relaxed">
                        At VoxLabs, we take your privacy seriously. This policy outlines how we collect, use, and protect your voice data and personal information.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4">Data Collection</h2>
                    <p>
                        We collect audio samples strictly for the purpose of voice cloning and synthesis as requested by you. Your voice data is encrypted at rest and in transit.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4">Data Usage</h2>
                    <p>
                        Your data is never sold to third parties. We use your data solely to provide the services you have requested.
                    </p>
                </div>
            </div>
        </div>
    )
}
