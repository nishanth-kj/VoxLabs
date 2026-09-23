"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api, SystemStatus, Voice } from "@/lib/api";
import {
  IconActivity,
  IconArrowRight,
  IconCpu,
  IconLibrary,
  IconLock,
  IconMic,
  IconPlus,
  IconSettings,
  IconSliders,
  IconSpeech,
  IconWaveform,
} from "@/components/icons";
import { Banner, Card, Page, WaveformBars, buttonStyles, cn } from "@/components/ui";

const TOOLS = [
  { href: "/studio", label: "Speech Studio", description: "Write, direct, render, and compare takes.", icon: IconSliders, accent: "from-indigo-500/20 to-violet-500/10" },
  { href: "/clone", label: "Voice Clone", description: "Create a consented voice identity from a sample.", icon: IconMic, accent: "from-violet-500/20 to-fuchsia-500/10" },
  { href: "/library", label: "Voice Library", description: "Manage voices, identities, and generated assets.", icon: IconLibrary, accent: "from-emerald-500/20 to-cyan-500/10" },
  { href: "/models", label: "AI Models", description: "See installed engines and model readiness.", icon: IconCpu, accent: "from-sky-500/20 to-indigo-500/10" },
  { href: "/tts", label: "Quick TTS", description: "Turn a short prompt into speech immediately.", icon: IconSpeech, accent: "from-amber-500/20 to-orange-500/10" },
];

export default function DashboardPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  useEffect(() => {
    api.getStatus()
      .then((data) => { setStatus(data); setStatusError(null); })
      .catch((e) => setStatusError(e.message));

    api.listVoices()
      .then((data) => { setVoices(data.voices); setVoiceError(null); })
      .catch((e) => setVoiceError(e.message));
  }, []);

  const backendLabel = statusError ? "Offline" : status ? "Connected" : "Checking";
  const engineLabel = status ? (status.engine_ready ? "Ready" : "Warming") : "—";
  const capabilityLabel = useMemo(() => {
    if (!status?.capabilities?.length) return "Local voice stack";
    return `${status.capabilities.length} capabilities`;
  }, [status]);

  return (
    <Page className="bg-[radial-gradient(circle_at_top_right,rgba(99,102,241,0.12),transparent_35%)]">
      {statusError && (
        <Banner tone="error">
          Could not reach the local API. Start the backend to enable generation. {statusError}
        </Banner>
      )}

      <section className="relative overflow-hidden rounded-3xl border border-border glass px-6 py-8 sm:px-8">
        <div className="pointer-events-none absolute -right-28 -top-28 h-64 w-64 rounded-full bg-indigo-500/15 blur-3xl" />
        <div className="relative grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface-alt/80 px-2.5 py-1 text-[11px] font-medium text-foreground-dim">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              Local AI voice workspace
            </div>
            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.03em] sm:text-5xl">
              Make audio sound intentional.
            </h1>
            <p className="mt-4 max-w-xl text-sm leading-7 text-foreground-dim sm:text-base">
              One focused workspace for voice cloning, expressive text-to-speech, model control, and production-ready audio.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              <Link href="/studio" className={buttonStyles("primary", "md")}>
                <IconSliders className="h-4 w-4" />
                Open Studio
              </Link>
              <Link href="/clone" className={buttonStyles("default", "md")}>
                <IconPlus className="h-4 w-4" />
                Create voice
              </Link>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-background/60 p-4 sm:p-5">
            <div className="flex items-center justify-between text-xs text-foreground-dim">
              <span>Live engine</span>
              <span className="font-mono">{status?.version ?? "local"}</span>
            </div>
            <div className="mt-5">
              <WaveformBars active className="h-28" />
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2">
              <MiniMetric label="Backend" value={backendLabel} />
              <MiniMetric label="Engine" value={engineLabel} />
              <MiniMetric label="Stack" value={capabilityLabel} />
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-end justify-between gap-4">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-foreground-dim">Workspace</p>
            <h2 className="mt-1 text-lg font-semibold tracking-tight">Everything in one place</h2>
          </div>
          <button type="button" className="hidden items-center gap-1.5 text-xs text-foreground-dim hover:text-foreground sm:inline-flex" onClick={() => window.dispatchEvent(new Event("voxlabs:settings"))}>
            <IconSettings className="h-3.5 w-3.5" />
            Configure
          </button>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {TOOLS.map((tool) => {
            const Icon = tool.icon;
            return (
              <Link key={tool.href} href={tool.href} className="group">
                <Card className="relative h-full overflow-hidden p-4 transition-colors group-hover:border-accent/30">
                  <div className={cn("absolute inset-x-0 top-0 h-20 bg-gradient-to-br opacity-80", tool.accent)} />
                  <div className="relative">
                    <div className="flex items-center justify-between">
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-surface text-foreground">
                        <Icon className="h-4 w-4" />
                      </div>
                      <IconArrowRight className="h-4 w-4 text-foreground-dim opacity-0 transition-opacity group-hover:opacity-100" />
                    </div>
                    <p className="mt-9 text-sm font-medium">{tool.label}</p>
                    <p className="mt-1 text-xs leading-5 text-foreground-dim">{tool.description}</p>
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-sm font-medium">Your voices</h2>
              <p className="mt-1 text-xs text-foreground-dim">Stored and managed on this machine.</p>
            </div>
            <Link href="/library" className="text-xs text-foreground-dim hover:text-foreground">View library</Link>
          </div>

          {voiceError && <p className="mt-5 text-sm text-danger">{voiceError}</p>}
          {!voiceError && voices.length === 0 && (
            <div className="mt-5 rounded-2xl border border-dashed border-border px-5 py-10 text-center">
              <IconMic className="mx-auto h-5 w-5 text-foreground-dim" />
              <p className="mt-3 text-sm font-medium">No voices yet</p>
              <p className="mt-1 text-xs text-foreground-dim">Create a voice to begin building your library.</p>
              <Link href="/clone" className="mt-4 inline-flex text-sm text-accent-hover hover:text-white">Create a voice</Link>
            </div>
          )}
          {!voiceError && voices.length > 0 && (
            <ul className="mt-4 divide-y divide-border">
              {voices.slice(0, 6).map((voice) => (
                <li key={voice.voice_id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                  <VoiceMark name={voice.name} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{voice.name}</p>
                    <p className="truncate font-mono text-[11px] text-foreground-dim">{voice.voice_id}</p>
                  </div>
                  <span className="text-[11px] text-foreground-dim">{voice.project_id ?? "default"}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-sm font-medium">System</h2>
              <p className="mt-1 text-xs text-foreground-dim">Runtime and model state.</p>
            </div>
            <IconActivity className="h-4 w-4 text-foreground-dim" />
          </div>
          <div className="mt-5 space-y-3">
            <SystemRow label="Backend" value={backendLabel} ok={!statusError} />
            <SystemRow label="Engine" value={engineLabel} ok={!!status?.engine_ready} />
            <SystemRow label="Version" value={status?.version ?? "—"} />
            <SystemRow label="Memory mode" value={status?.memory_optimization ?? "—"} />
          </div>
          <div className="mt-5 rounded-2xl border border-border bg-surface-alt/60 p-3.5">
            <p className="flex items-center gap-1.5 text-xs font-medium">
              <IconLock className="h-3.5 w-3.5 text-success" />
              Local-first
            </p>
            <p className="mt-1 text-xs leading-5 text-foreground-dim">
              Voice samples and generated audio stay on the machine unless you explicitly add an external integration.
            </p>
          </div>
        </Card>
      </div>
    </Page>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface-alt/70 px-3 py-2">
      <p className="text-[10px] text-foreground-dim">{label}</p>
      <p className="mt-0.5 truncate text-xs font-medium">{value}</p>
    </div>
  );
}

function SystemRow({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border pb-3 last:border-0 last:pb-0">
      <span className="text-xs text-foreground-dim">{label}</span>
      <span className="inline-flex max-w-[60%] items-center gap-1.5 truncate text-xs font-medium">
        {ok !== undefined && <span className={cn("h-1.5 w-1.5 rounded-full", ok ? "bg-success" : "bg-danger")} />}
        {value}
      </span>
    </div>
  );
}

function VoiceMark({ name }: { name: string }) {
  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");

  return (
    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent-soft text-[11px] font-semibold text-accent-hover">
      {initials || "V"}
    </div>
  );
}
