export default function TermsPage() {
    return (
        <div className="min-h-screen bg-background text-foreground pt-32 pb-20 px-6">
            <div className="max-w-3xl mx-auto space-y-8">
                <h1 className="text-4xl font-bold tracking-tight mb-8">Terms of Service</h1>

                <div className="prose dark:prose-invert max-w-none">
                    <p className="text-muted-foreground text-lg leading-relaxed">
                        By using VoxLabs, you agree to these terms. Please read them carefully.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4">Usage Limits</h2>
                    <p>
                        You agree not to use our service to generate content that is illegal, harmful, or violates the rights of others.
                    </p>

                    <h2 className="text-2xl font-semibold mt-8 mb-4">Intellectual Property</h2>
                    <p>
                        You retain rights to the content you generate, subject to our usage guidelines.
                    </p>
                </div>
            </div>
        </div>
    )
}
