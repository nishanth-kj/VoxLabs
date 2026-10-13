'use client'

import { useState } from 'react'
import { getBasePath, SITE_VERSION } from '@/lib/site'
import { Sparkles, FolderOpen, Bot, Gauge } from 'lucide-react'

export const DESKTOP_VIEWS = [
  {
    id: 'generate',
    label: 'Text to Speech',
    icon: Sparkles,
    src: '/screenshots/generate.png',
    alt: 'VoxLabs desktop Text to Speech interface showing sentence breakdown, voice selection, emotion delivery controls, and real-time generation factor',
    badge: 'Sentence TTS · RTF 0.35x',
    caption: 'Sentence-by-sentence synthesis with inline emotion, custom pronunciations, and real-time factor metrics.',
  },
  {
    id: 'files',
    label: 'Files & Library',
    icon: FolderOpen,
    src: '/screenshots/files.png',
    alt: 'VoxLabs desktop Central Library listing generated, imported, edited audio and export destinations with folders',
    badge: 'Central Audio Library',
    caption: 'Every audio file in one place: generated takes, imported tracks, non-destructive edits, and format exports.',
  },
  {
    id: 'mcp',
    label: 'MCP Server',
    icon: Bot,
    src: '/screenshots/mcp.png',
    alt: 'VoxLabs desktop MCP page with real-time log of Claude and AI agent tool invocations, duration, and parameter inspector',
    badge: '30 MCP Tools · Live Log',
    caption: 'Built-in Model Context Protocol server: live activity log of every tool call from Claude Desktop and AI agents.',
  },
  {
    id: 'performance',
    label: 'Performance',
    icon: Gauge,
    src: '/screenshots/performance.png',
    alt: 'VoxLabs desktop Performance page displaying detected NVIDIA GPU VRAM, system RAM, and recommended presets',
    badge: 'GPU & RAM Presets',
    caption: 'Hardware-detected presets (Quality, Balanced, Fast, Low Memory) with automatic GPU memory recycling.',
  },
] as const

export function DesktopPreview() {
  const [activeId, setActiveId] = useState<string>(DESKTOP_VIEWS[0].id)
  const basePath = getBasePath()
  const activeView = DESKTOP_VIEWS.find((v) => v.id === activeId) ?? DESKTOP_VIEWS[0]

  return (
    <div className="relative mx-auto w-full max-w-5xl pt-4">
      {/* Ambient background glow */}
      <div className="absolute -inset-6 rounded-3xl bg-gradient-to-tr from-indigo-500/20 via-purple-500/10 to-pink-500/10 blur-3xl pointer-events-none" />

      <div className="relative rounded-2xl border border-border/60 bg-card/90 shadow-2xl shadow-indigo-950/20 overflow-hidden backdrop-blur-md">
        {/* Desktop window title bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-border/50 bg-secondary/60">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-red-400/80 inline-block shadow-sm" />
            <span className="h-3 w-3 rounded-full bg-yellow-400/80 inline-block shadow-sm" />
            <span className="h-3 w-3 rounded-full bg-emerald-400/80 inline-block shadow-sm" />
            <div className="flex items-center gap-2 ml-3">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#6352f0"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4 w-4 shrink-0"
                aria-hidden="true"
              >
                <rect x="1" y="1" width="22" height="22" rx="6" fill="#6352f0" stroke="none" />
                <path d="M7 10v4M10 7v10M13 9v6M16 11v2" stroke="#ffffff" strokeWidth="2.2" />
              </svg>
              <span className="text-xs font-semibold text-foreground tracking-tight">VoxLabs Desktop</span>
              <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                v{SITE_VERSION}
              </span>
            </div>
          </div>

          {/* View switcher tabs right in the title bar */}
          <div className="flex items-center gap-1 bg-background/80 p-1 rounded-lg border border-border/40 shadow-inner">
            {DESKTOP_VIEWS.map((view) => {
              const Icon = view.icon
              const isActive = view.id === activeId
              return (
                <button
                  key={view.id}
                  type="button"
                  onClick={() => setActiveId(view.id)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground hover:bg-secondary/60'
                  }`}
                  aria-pressed={isActive}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">{view.label}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Real desktop screenshot display */}
        <div className="relative bg-muted/30">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`${basePath}${activeView.src}`}
            alt={activeView.alt}
            width={1800}
            height={1100}
            loading="eager"
            className="w-full h-auto block object-cover transition-opacity duration-300"
          />
        </div>

        {/* Bottom feature pill and description */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-5 py-3 border-t border-border/40 bg-card/70 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-medium text-emerald-500 border border-emerald-500/20">
              ● Local Execution
            </span>
            <span className="font-medium text-foreground">{activeView.badge}</span>
          </div>
          <p className="text-center sm:text-right">{activeView.caption}</p>
        </div>
      </div>
    </div>
  )
}
