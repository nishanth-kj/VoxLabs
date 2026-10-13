'use client'

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { getBasePath } from "@/lib/site"

// Real screenshots of the desktop app (docs/images in the repository, copied to public/screenshots).
export const SCREENSHOTS = [
  {
    id: "generate",
    label: "Text to speech",
    src: "/screenshots/generate.png",
    alt: "VoxLabs Generate page: text split into sentences, voice and delivery settings, and the measured timings of the generation",
    caption: "Generate speech sentence by sentence, regenerate any one of them, and see the real speed of every run.",
  },
  {
    id: "files",
    label: "Files",
    src: "/screenshots/files.png",
    alt: "VoxLabs Files page listing generated, edited and exported audio with their folders",
    caption: "Everything VoxLabs keeps in one list: generated, imported and edited audio, every export and voice samples.",
  },
  {
    id: "mcp",
    label: "MCP log",
    src: "/screenshots/mcp.png",
    alt: "VoxLabs MCP page with a live log of AI agent tool calls, their arguments and errors",
    caption: "Every call an AI app makes through MCP, with its arguments, result or error, and how long it took.",
  },
  {
    id: "performance",
    label: "Performance",
    src: "/screenshots/performance.png",
    alt: "VoxLabs performance settings with detected GPU, VRAM and RAM and the recommended preset",
    caption: "Quality, Balanced, Fast or Low Memory, with the preset recommended for the hardware VoxLabs detects.",
  },
] as const

export function ScreenshotsSection() {
  const basePath = getBasePath()

  return (
    <section id="screenshots" className="py-20 px-6 bg-background border-t border-border/40">
      <div className="max-w-6xl mx-auto space-y-10">
        <div className="text-center space-y-4">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">See It in Action</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Real screenshots of the desktop app. One window for speech, scripts, editing, files and models.
          </p>
        </div>

        <Tabs defaultValue={SCREENSHOTS[0].id} className="items-center gap-6">
          <TabsList className="flex-wrap h-auto">
            {SCREENSHOTS.map((shot) => (
              <TabsTrigger key={shot.id} value={shot.id}>
                {shot.label}
              </TabsTrigger>
            ))}
          </TabsList>
          {SCREENSHOTS.map((shot) => (
            <TabsContent key={shot.id} value={shot.id} className="w-full space-y-4">
              <div className="relative mx-auto w-full">
                <div className="absolute -inset-4 rounded-3xl bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent blur-2xl pointer-events-none" />
                {/* Static export (next.config: images.unoptimized), so a plain img with the base path. */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={`${basePath}${shot.src}`}
                  alt={shot.alt}
                  width={1800}
                  height={1100}
                  loading="lazy"
                  className="relative w-full h-auto rounded-xl border border-border/40 shadow-2xl"
                />
              </div>
              <p className="text-center text-sm text-muted-foreground">{shot.caption}</p>
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </section>
  )
}
