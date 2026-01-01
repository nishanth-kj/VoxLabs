import { Button } from "@/components/ui/button"
import { ArrowRight, Book, FileText, Code, Settings, Terminal, AlertTriangle, CheckCircle2, Copy } from "lucide-react"
import Link from "next/link"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function DocsPage() {
    return (
        <div className="min-h-screen bg-background text-foreground pt-24 pb-20 px-6">
            <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-12">

                {/* Sidebar Navigation */}
                <aside className="hidden md:block md:col-span-3 lg:col-span-2 space-y-8 sticky top-32 h-[calc(100vh-8rem)] overflow-y-auto pr-4 scrollbar-thin">
                    <div className="space-y-4">
                        <h3 className="font-semibold text-lg flex items-center gap-2">
                            <Book className="w-4 h-4 text-primary" />
                            Getting Started
                        </h3>
                        <nav className="flex flex-col space-y-2 text-sm text-muted-foreground ml-6 border-l border-border/40 pl-4">
                            <Link href="#introduction" className="hover:text-foreground transition-colors">Introduction</Link>
                            <Link href="#installation" className="hover:text-foreground transition-colors">Installation</Link>
                            <Link href="#quick-start" className="hover:text-foreground transition-colors">Quick Start</Link>
                        </nav>
                    </div>

                    <div className="space-y-4">
                        <h3 className="font-semibold text-lg flex items-center gap-2">
                            <Code className="w-4 h-4 text-primary" />
                            API Reference
                        </h3>
                        <nav className="flex flex-col space-y-2 text-sm text-muted-foreground ml-6 border-l border-border/40 pl-4">
                            <Link href="#authentication" className="hover:text-foreground transition-colors">Authentication</Link>
                            <Link href="#endpoints" className="hover:text-foreground transition-colors">Endpoints</Link>
                            <Link href="#errors" className="hover:text-foreground transition-colors">Error Handling</Link>
                        </nav>
                    </div>
                    <div className="space-y-4">
                        <h3 className="font-semibold text-lg flex items-center gap-2">
                            <Settings className="w-4 h-4 text-primary" />
                            Guides
                        </h3>
                        <nav className="flex flex-col space-y-2 text-sm text-muted-foreground ml-6 border-l border-border/40 pl-4">
                            <Link href="#voice-cloning" className="hover:text-foreground transition-colors">Voice Cloning</Link>
                            <Link href="#emotion-control" className="hover:text-foreground transition-colors">Emotion Control</Link>
                            <Link href="#best-practices" className="hover:text-foreground transition-colors">Best Practices</Link>
                        </nav>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="md:col-span-9 lg:col-span-10 space-y-20">

                    {/* Header */}
                    <div className="space-y-6 border-b border-border/40 pb-12">
                        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">Documentation</h1>
                        <p className="text-xl text-muted-foreground leading-relaxed max-w-3xl">
                            Everything you need to build with VoxLabs.
                        </p>
                        <div className="flex gap-4">
                            <Link href="#quick-start">
                                <Button>
                                    Start Building
                                    <ArrowRight className="ml-2 w-4 h-4" />
                                </Button>
                            </Link>
                        </div>
                    </div>

                    {/* Getting Started */}
                    <section id="introduction" className="scroll-mt-32 space-y-6">
                        <h2 className="text-3xl font-bold flex items-center gap-3">
                            Introduction
                            <div className="h-px bg-border/60 flex-1 ml-4" />
                        </h2>
                        <p className="text-muted-foreground leading-relaxed text-lg">
                            VoxLabs is a next-generation voice synthesis engine designed for developers who need <strong>emotional control</strong> and <strong>low-latency</strong> performance. Unlike traditional TTS, VoxLabs uses advanced neural vocoders to generate speech that captures the subtleties of human expression.
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FeatureItem title="Emotional Intelligence" description="Control pitch, speed, and energy to convey specific moods." />
                            <FeatureItem title="Zero-Shot Cloning" description="Clone voices with just 30 seconds of reference audio." />
                            <FeatureItem title="Streaming API" description="Real-time audio generation for conversational AI." />
                            <FeatureItem title="Privacy First" description="Voice data is encrypted and isolated." />
                        </div>
                    </section>

                    <section id="installation" className="scroll-mt-32 space-y-6">
                        <h2 className="text-3xl font-bold flex items-center gap-3">
                            Installation
                            <div className="h-px bg-border/60 flex-1 ml-4" />
                        </h2>
                        <p className="text-muted-foreground">
                            Install our official Python SDK to get started immediately.
                        </p>
                        <div className="bg-slate-950 rounded-lg border border-border/40 p-4">
                            <div className="flex items-center justify-between text-muted-foreground mb-2 text-xs font-mono">
                                <span>Terminal</span>
                                <Copy className="w-3 h-3 cursor-pointer hover:text-white" />
                            </div>
                            <code className="text-sm font-mono text-green-400">pip install voxlabs-sdk</code>
                        </div>
                    </section>

                    <section id="quick-start" className="scroll-mt-32 space-y-6">
                        <h2 className="text-3xl font-bold flex items-center gap-3">
                            Quick Start
                            <div className="h-px bg-border/60 flex-1 ml-4" />
                        </h2>
                        <p className="text-muted-foreground">
                            Generate your first audio file in less than 5 minutes.
                        </p>
                        <CodeBlock language="python" code={`from voxlabs import VoxClient

client = VoxClient(api_key="your_api_key")

# Generate speech
audio = client.tts.create(
    text="Hello! I can speak with real emotion.",
    emotion="happy",
    voice_id="en-us-1"
)

# Save to file
audio.save("hello.mp3")`} />
                    </section>

                    {/* API Reference */}
                    <section id="authentication" className="scroll-mt-32 space-y-6">
                        <h2 className="text-3xl font-bold flex items-center gap-3">
                            Authentication
                            <div className="h-px bg-border/60 flex-1 ml-4" />
                        </h2>
                        <p className="text-muted-foreground">
                            All API requests must include your API key in the <code className="bg-secondary px-1.5 py-0.5 rounded text-foreground font-mono text-sm">Authorization</code> header.
                        </p>
                        <div className="bg-slate-950 rounded-lg border border-border/40 p-4">
                            <code className="text-sm font-mono text-blue-300">Authorization: Bearer YOUR_API_KEY</code>
                        </div>
                    </section>

                    <section id="endpoints" className="scroll-mt-32 space-y-6">
                        <h2 className="text-3xl font-bold flex items-center gap-3">
                            Endpoints
                            <div className="h-px bg-border/60 flex-1 ml-4" />
                        </h2>
                        <div className="space-y-4">
                            <EndpointMethod method="POST" path="/v1/tts" description="Generate speech from text." />
                            <EndpointMethod method="GET" path="/v1/voices" description="List available voices." />
                            <EndpointMethod method="POST" path="/v1/voices/clone" description="Create a custom voice clone." />
                        </div>
                    </section>

                    <section id="errors" className="scroll-mt-32 space-y-6">
                        <h2 className="text-3xl font-bold flex items-center gap-3">
                            Error Handling
                            <div className="h-px bg-border/60 flex-1 ml-4" />
                        </h2>
                        <p className="text-muted-foreground">
                            VoxLabs uses standard HTTP status codes to indicate the success or failure of requests.
                        </p>
                        <div className="grid grid-cols-1 gap-4">
                            <ErrorItem code="400" title="Bad Request" description="Invalid input parameters or audio format." />
                            <ErrorItem code="401" title="Unauthorized" description="Missing or invalid API key." />
                            <ErrorItem code="429" title="Rate Limit Exceeded" description="You have made too many requests. Please wait." />
                        </div>
                    </section>

                    {/* Guides */}
                    <section id="voice-cloning" className="scroll-mt-32 space-y-6">
                        <h2 className="text-3xl font-bold flex items-center gap-3">
                            Voice Cloning Guide
                            <div className="h-px bg-border/60 flex-1 ml-4" />
                        </h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Our cloning engine requires high-quality audio samples to create accurate voice models. For best results, upload at least <strong>30 seconds</strong> of clean speech without background noise.
                        </p>
                        <div className="bg-secondary/20 border border-indigo-500/20 rounded-xl p-6">
                            <h4 className="font-semibold mb-4 flex items-center gap-2">
                                <CheckCircle2 className="w-5 h-5 text-indigo-400" />
                                Requirements
                            </h4>
                            <ul className="space-y-2 text-sm text-muted-foreground">
                                <li>• Format: WAV or MP3 (44.1kHz+)</li>
                                <li>• Duration: 30s - 5min</li>
                                <li>• Content: Natural, flowing speech</li>
                                <li>• Noise: Minimal background noise/reverb</li>
                            </ul>
                        </div>
                    </section>

                    <section id="emotion-control" className="scroll-mt-32 space-y-6">
                        <h2 className="text-3xl font-bold flex items-center gap-3">
                            Emotion Control
                            <div className="h-px bg-border/60 flex-1 ml-4" />
                        </h2>
                        <p className="text-muted-foreground">
                            You can direct the emotional tone of the generated speech using the <code className="font-mono text-sm">emotion</code> parameter.
                        </p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {['Happy', 'Sad', 'Angry', 'Fearful', 'Excited', 'Whisper', 'Shout', 'Neutral'].map((emotion) => (
                                <div key={emotion} className="p-3 border border-border/40 rounded-lg text-center text-sm font-medium hover:bg-secondary/50 transition-colors cursor-default">
                                    {emotion}
                                </div>
                            ))}
                        </div>
                    </section>

                    <section id="best-practices" className="scroll-mt-32 space-y-6">
                        <h2 className="text-3xl font-bold flex items-center gap-3">
                            Best Practices
                            <div className="h-px bg-border/60 flex-1 ml-4" />
                        </h2>
                        <div className="space-y-4">
                            <div className="flex gap-4 p-4 bg-secondary/10 rounded-lg border border-border/40">
                                <Terminal className="w-6 h-6 text-primary shrink-0" />
                                <div>
                                    <h4 className="font-semibold text-foreground">Cache Generated Audio</h4>
                                    <p className="text-sm text-muted-foreground mt-1">TTS generation is computationally expensive. Always cache results for identical text/voice combinations.</p>
                                </div>
                            </div>
                            <div className="flex gap-4 p-4 bg-secondary/10 rounded-lg border border-border/40">
                                <AlertTriangle className="w-6 h-6 text-yellow-500 shrink-0" />
                                <div>
                                    <h4 className="font-semibold text-foreground">Streaming for Long Text</h4>
                                    <p className="text-sm text-muted-foreground mt-1">For long paragraphs, use the streaming endpoint to play audio immediately as it's generated, reducing perceived latency.</p>
                                </div>
                            </div>
                        </div>
                    </section>

                </main>
            </div>
        </div>
    )
}

function FeatureItem({ title, description }: { title: string, description: string }) {
    return (
        <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-secondary/20 transition-colors">
            <CheckCircle2 className="w-5 h-5 text-indigo-500 mt-0.5" />
            <div>
                <h4 className="font-semibold text-sm">{title}</h4>
                <p className="text-xs text-muted-foreground">{description}</p>
            </div>
        </div>
    )
}

function CodeBlock({ language, code }: { language: string, code: string }) {
    return (
        <div className="bg-slate-950 rounded-lg border border-border/40 overflow-hidden">
            <div className="bg-white/5 px-4 py-2 border-b border-white/5 flex items-center justify-between">
                <span className="text-xs font-mono text-muted-foreground uppercase">{language}</span>
            </div>
            <pre className="p-4 overflow-x-auto text-sm font-mono text-blue-100 leading-relaxed">
                {code}
            </pre>
        </div>
    )
}

function EndpointMethod({ method, path, description }: { method: string, path: string, description: string }) {
    const color = {
        'GET': 'text-blue-400 bg-blue-500/10 border-blue-500/20',
        'POST': 'text-green-400 bg-green-500/10 border-green-500/20',
        'DELETE': 'text-red-400 bg-red-500/10 border-red-500/20',
        'PUT': 'text-orange-400 bg-orange-500/10 border-orange-500/20',
    }[method] || 'text-muted-foreground'

    return (
        <div className="flex items-center gap-4 p-4 bg-card border border-border/40 rounded-lg">
            <span className={`px-3 py-1 rounded text-xs font-bold border ${color} w-20 text-center`}>
                {method}
            </span>
            <code className="text-sm font-mono text-foreground flex-1">{path}</code>
            <span className="text-sm text-muted-foreground md:block hidden">{description}</span>
        </div>
    )
}

function ErrorItem({ code, title, description }: { code: string, title: string, description: string }) {
    return (
        <div className="flex items-start gap-4 p-4 border border-border/40 rounded-lg">
            <span className="font-mono text-sm font-bold text-red-400">{code}</span>
            <div>
                <h4 className="font-semibold text-sm">{title}</h4>
                <p className="text-sm text-muted-foreground mt-1">{description}</p>
            </div>
        </div>
    )
}
