import type { ReactNode } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Mic, Wand2, Lock, FileText, Sliders, Terminal } from "lucide-react"

import { HeroSection } from "@/components/landing/hero-section"
import { HowItWorksSection } from "@/components/landing/how-it-works-section"
import { DownloadSection } from "@/components/landing/download-section"
import { JsonLd } from "@/components/json-ld"
import { ENGINE_SPECS, HOME_JSON_LD, SITE_FAQS } from "@/lib/site"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-50/50 via-background to-background dark:from-slate-900 dark:via-background dark:to-background selection:bg-primary/20">

      <JsonLd data={HOME_JSON_LD} />
      <HeroSection />

      <section id="features" className="py-20 px-6 bg-secondary/30 border-t border-border/40 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Why VoxLabs?</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              A complete local desktop voice studio for creators, educators, and developers who want expressive speech without sending audio to the cloud.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Wand2 className="w-6 h-6 text-indigo-400" />}
              title="Emotional TTS"
              description="Generate speech with granular control over emotion, style, speed, pitch, energy, pauses, and custom pronunciations—with deterministic caching."
            />
            <FeatureCard
              icon={<Mic className="w-6 h-6 text-purple-400" />}
              title="Instant Voice Cloning"
              description="Clone a voice from a short reference sample with mandatory speaker consent. Revoking consent immediately deletes samples and voice profiles."
            />
            <FeatureCard
              icon={<FileText className="w-6 h-6 text-pink-400" />}
              title="Script & Lesson to Audio"
              description="Turn multi-speaker scripts and chapters into narrated audio with per-section voice overrides, multiple takes, and unchanged-section caching."
            />
            <FeatureCard
              icon={<Sliders className="w-6 h-6 text-amber-400" />}
              title="Non-Destructive Audio Editor"
              description="Edit on a live waveform with instant undo/redo, plus an 8-stage DSP mastering pipeline (spectral denoise, RBJ EQ, de-esser, BS.1770 LUFS)."
            />
            <FeatureCard
              icon={<Lock className="w-6 h-6 text-emerald-400" />}
              title="Local & Private by Default"
              description="Run Piper, Kokoro 82M, Chatterbox, Chatterbox Turbo, and Qwen3-TTS 0.6B on your CPU or CUDA GPU (with automatic CPU fallback when VRAM is full)."
            />
            <FeatureCard
              icon={<Terminal className="w-6 h-6 text-cyan-400" />}
              title="REST API & MCP Server"
              description="Automate speech generation, script rendering, and DSP enhancement from external tools or AI agents via localhost REST API and MCP (--stdio & /mcp)."
            />
          </div>
        </div>
      </section>

      <section id="engines" className="py-20 px-6 bg-background border-t border-border/40">
        <div className="max-w-5xl mx-auto space-y-10">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              Supported Local AI Engines &amp; DSP
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Install lightweight CPU voices or full zero-shot GPU cloning models directly from the Models page inside the desktop app.
            </p>
          </div>

          <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4 shadow-sm">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Engine</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Download Size</TableHead>
                  <TableHead>Compute</TableHead>
                  <TableHead>Capabilities</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ENGINE_SPECS.map((engine) => (
                  <TableRow key={engine.name}>
                    <TableCell className="font-semibold">{engine.name}</TableCell>
                    <TableCell className="text-muted-foreground">{engine.type}</TableCell>
                    <TableCell className="font-mono text-xs">{engine.size}</TableCell>
                    <TableCell className="text-muted-foreground text-xs">{engine.compute}</TableCell>
                    <TableCell className="text-muted-foreground text-sm whitespace-normal">
                      {engine.highlights}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </section>

      <HowItWorksSection />

      <section id="faq" className="py-20 px-6 bg-background border-t border-border/40">
        <div className="max-w-4xl mx-auto space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              Frequently Asked Questions
            </h2>
            <p className="text-muted-foreground">
              Everything you need to know about running VoxLabs locally on your machine.
            </p>
          </div>

          <dl className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {SITE_FAQS.map((item) => (
              <div
                key={item.question}
                className="rounded-xl border border-border/40 bg-card/50 p-6 space-y-3"
              >
                <dt className="text-base font-semibold text-foreground leading-snug">
                  {item.question}
                </dt>
                <dd className="text-sm text-muted-foreground leading-relaxed">
                  {item.answer}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <DownloadSection />

    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: ReactNode, title: string, description: string }) {
  return (
    <Card className="bg-card/50 border-border/40 hover:border-border/80 transition-colors h-full">
      <CardHeader>
        <div className="w-12 h-12 rounded-lg bg-secondary flex items-center justify-center mb-4">
          {icon}
        </div>
        <CardTitle className="text-xl">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground leading-relaxed">
          {description}
        </p>
      </CardContent>
    </Card>
  )
}
