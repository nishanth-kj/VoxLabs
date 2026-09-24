import type { ReactNode } from "react"
import { Download, Mic, Sparkles, HardDrive } from "lucide-react"

export function HowItWorksSection() {
    return (
        <section id="how-it-works" className="py-24 px-6 bg-background relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-500/5 via-transparent to-transparent pointer-events-none" />

            <div className="max-w-7xl mx-auto space-y-16 relative z-10">
                <div className="text-center space-y-6">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-500/10 mb-4 border border-blue-500/20">
                        <HardDrive className="w-8 h-8 text-blue-500" />
                    </div>
                    <h2 className="text-3xl md:text-5xl font-bold tracking-tight">
                        How VoxLabs Works
                    </h2>
                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                        Install the desktop app. Clone with consent. Synthesize locally. Your voice never leaves the machine.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 relative">
                    <div className="hidden lg:block absolute top-12 left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-indigo-500/0 via-indigo-500/20 to-indigo-500/0 z-0"></div>

                    <StepCard
                        number="01"
                        icon={<Download className="w-6 h-6 text-indigo-400" />}
                        title="Download"
                        description="Install VoxLabs for Windows, macOS, or Linux. One app — no browser account, no cloud workspace."
                    />
                    <StepCard
                        number="02"
                        icon={<Mic className="w-6 h-6 text-purple-400" />}
                        title="Consent & clone"
                        description="Record or import about 30 seconds of audio. Cloning requires explicit consent every time."
                    />
                    <StepCard
                        number="03"
                        icon={<Sparkles className="w-6 h-6 text-pink-400" />}
                        title="Synthesize"
                        description="Type text, pick an emotion, and generate speech with control over speed, pitch, and energy."
                    />
                    <StepCard
                        number="04"
                        icon={<HardDrive className="w-6 h-6 text-emerald-400" />}
                        title="Stay local"
                        description="Audio is processed on your computer and labeled as AI-generated. Delete a voice anytime."
                    />
                </div>
            </div>
        </section>
    )
}

function StepCard({ number, icon, title, description }: { number: string, icon: ReactNode, title: string, description: string }) {
    return (
        <div className="relative z-10 bg-card/50 backdrop-blur-sm border border-border/40 rounded-xl p-6 space-y-4 hover:border-primary/50 transition-colors shadow-lg group">
            <div className="flex items-center justify-between">
                <div className="w-12 h-12 rounded-lg bg-secondary flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    {icon}
                </div>
                <span className="text-4xl font-bold text-muted-foreground/10">{number}</span>
            </div>
            <h3 className="text-xl font-bold">{title}</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
                {description}
            </p>
        </div>
    )
}
