'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Mic, Wand2, Lock } from "lucide-react"
import { gsap } from "gsap"
import { useGSAP } from "@gsap/react"
import { useRef } from 'react'

import { HeroSection } from "@/components/landing/hero-section"
import { HowItWorksSection } from "@/components/landing/how-it-works-section"
import { ApiSection } from "@/components/landing/api-section"

export default function LandingPage() {
  const containerRef = useRef<HTMLDivElement>(null)
  const featuresRef = useRef<HTMLDivElement>(null)

  useGSAP(() => {
    const tl = gsap.timeline()

    tl.from(featuresRef.current?.children || [], {
      y: 50,
      opacity: 0,
      duration: 0.8,
      stagger: 0.2,
      ease: "power3.out",
      delay: 0.5
    })

  }, { scope: containerRef })

  return (
    <div ref={containerRef} className="min-h-screen bg-background text-foreground bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-50/50 via-background to-background dark:from-slate-900 dark:via-background dark:to-background selection:bg-primary/20">

      {/* Hero Section */}
      <HeroSection />



      <section className="py-20 px-6 bg-secondary/30 border-t border-border/40 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Why VoxLabs?</h2>
            <p className="text-muted-foreground">Professional tools for creators, developers, and businesses.</p>
          </div>

          <div ref={featuresRef} className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Wand2 className="w-6 h-6 text-indigo-400" />}
              title="Emotional TTS"
              description="Generate speech with granular control over emotion, speed, pitch, and energy. Not just reading, but performing."
            />
            <FeatureCard
              icon={<Mic className="w-6 h-6 text-purple-400" />}
              title="Instant Voice Cloning"
              description="Clone any voice from a 30-second audio sample. Perfect for narrations, podcasts, and digital avatars."
            />
            <FeatureCard
              icon={<Lock className="w-6 h-6 text-emerald-400" />}
              title="Secure & Private"
              description="Your voice data is encrypted and never shared. We prioritize ethical AI usage and data protection."
            />
          </div>
        </div>
      </section>

      <HowItWorksSection />
      <ApiSection style={{ paddingBottom: '150px' }} />



    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
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
