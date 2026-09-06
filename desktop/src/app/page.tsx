"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { api, SystemStatus, Voice } from "@/lib/api";
import {
  IconActivity,
  IconArrowRight,
  IconLibrary,
  IconLock,
  IconMic,
  IconPlus,
  IconSpeech,
} from "@/components/icons";
import { Banner, Card, Page, WaveformBars, buttonStyles, cn } from "@/components/ui";

export default function DashboardPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getStatus()
      .then((data) => {
        setStatus(data);
        setStatusError(null);
      })
      .catch((e) => setStatusError(e.message));

    api
      .listVoices()
      .then((data) => {
        setVoices(data.voices);
        setVoiceError(null);
      })
      .catch((e) => setVoiceError(e.message));
  }, []);

  const backendLabel = statusError ? "Offline" : status ? "Connected" : "Checking";
  const engineLabel = status ? (status.engine_ready ? "Ready" : "Warming") : "—";

  return (
    <Page>
      {statusError && (
        <Banner tone="error">
          Could not reach the backend. Start the API, then reopen Studio. {statusError}
        </Banner>
      )}

      <section className="relative overflow-hidden rounded-2xl border border-border glass px-7 py-7">
        <div className="pointer-events-none absolute -top-24 right-0 h-56 w-56 rounded-full bg-indigo-500/20 blur-3xl" />
        <div className="relative grid items-center gap-8 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-foreground-dim">Overview</p>
            <h1 className="mt-2 text-[32px] leading-tight font-semibold tracking-tight">Your voice, locally.</h1>
            <p className="mt-2 max-w-md text-sm leading-relaxed text-foreground-dim">
              Clone with consent and generate emotional speech on this machine. Nothing is uploaded.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <Link href="/clone" className={buttonStyles("primary")}>
                <IconPlus className="h-3.5 w-3.5" />
                Clone a voice
              </Link>
              <Link href="/studio" className={buttonStyles("default")}>
                <IconSpeech className="h-3.5 w-3.5" />
                Open studio
              </Link>
            </div>
          </div>
          <WaveformBars active className="h-24 opacity-90" />
        </div>
      </section>

      <Card className="grid grid-cols-2 gap-0 p-0 min-[1100px]:grid-cols-4">
        <Metric label="Backend" value={backendLabel} hint="Local API" tone={statusError ? "danger" : status ? "success" : undefined} />
        <Metric label="Version" value={status?.version ?? "—"} hint="Engine build" />
        <Metric label="Voices" value={voiceError ? "—" : String(voices.length)} hint="On this machine" />
        <Metric label="Engine" value={engineLabel} hint={status?.memory_optimization ?? "Emotional TTS"} tone={status?.engine_ready ? "success" : undefined} last />
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <QuickAction
          href="/clone"
          icon={<IconMic className="h-4 w-4" />}
          well="bg-indigo-500/15 text-indigo-300"
          title="Clone a voice"
          description="Register a consented sample or design one from a prompt."
        />
        <QuickAction
          href="/studio"
          icon={<IconSpeech className="h-4 w-4" />}
          well="bg-violet-500/15 text-violet-300"
          title="Open studio"
          description="Write a script, pick a voice, and render takes with emotion and pitch."
        />
        <QuickAction
          href="/library"
          icon={<IconLibrary className="h-4 w-4" />}
          well="bg-emerald-500/15 text-emerald-300"
          title="Voice library"
          description="Review cloned voices and revoke any you no longer need."
        />
      </div>

      <div className="grid gap-4 min-[1100px]:grid-cols-[1.4fr_1fr]">
        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium">Recent voices</h2>
              <p className="mt-0.5 text-xs text-foreground-dim">Stored locally on this computer.</p>
            </div>
            <Link href="/library" className="text-xs text-foreground-dim hover:text-foreground">
              View all
            </Link>
          </div>
          {voiceError && <p className="text-sm text-danger">{voiceError}</p>}
          {!voiceError && voices.length === 0 && (
            <div className="rounded-xl border border-dashed border-border px-4 py-8 text-center">
              <p className="text-sm text-foreground-dim">No voices yet. Clone one to get started.</p>
              <Link href="/clone" className="mt-3 inline-flex text-sm text-accent-hover hover:text-white">
                Clone a voice
              </Link>
            </div>
          )}
          {!voiceError && voices.length > 0 && (
            <ul className="divide-y divide-border">
              {voices.slice(0, 5).map((voice) => (
                <li key={voice.voice_id} className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
                  <VoiceMark name={voice.name} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{voice.name}</p>
                    <p className="truncate font-mono text-[11px] text-foreground-dim">{voice.voice_id}</p>
                  </div>
                  <span className="text-xs text-foreground-dim">{voice.project_id ?? "default"}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="flex flex-col gap-4">
          <div>
            <h2 className="text-sm font-medium">Capabilities</h2>
            <p className="mt-0.5 text-xs text-foreground-dim">What this engine can do right now.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {status?.capabilities?.length ? (
              status.capabilities.map((cap) => (
                <span
                  key={cap}
                  className="inline-flex items-center gap-1.5 rounded-full border border-accent/25 bg-accent-soft px-2.5 py-1 text-[11px] font-medium text-accent-hover"
                >
                  <IconActivity className="h-3 w-3" />
                  {cap.replace(/_/g, " ")}
                </span>
              ))
            ) : (
              <span className="text-sm text-foreground-dim">
                {statusError ? "Unavailable while offline." : "Waiting for engine…"}
              </span>
            )}
          </div>
          <div className="mt-auto rounded-xl border border-border bg-surface-alt/50 px-3.5 py-3">
            <p className="flex items-center gap-1.5 text-xs font-medium">
              <IconLock className="h-3.5 w-3.5 text-success" />
              Stays on this machine
            </p>
            <p className="mt-1 text-xs leading-relaxed text-foreground-dim">
              Voice samples and generated audio are processed locally. Generated speech is labeled as AI-generated.
            </p>
          </div>
        </Card>
      </div>
    </Page>
  );
}

function Metric({
  label,
  value,
  hint,
  tone,
  last,
}: {
  label: string;
  value: string;
  hint: string;
  tone?: "success" | "danger";
  last?: boolean;
}) {
  return (
    <div className={cn("flex flex-col gap-1 px-5 py-4", !last && "lg:border-r lg:border-border")}>
      <p className="text-[11px] text-foreground-dim">{label}</p>
      <p
        className={cn(
          "truncate text-[22px] font-semibold tracking-tight",
          tone === "success" && "text-success",
          tone === "danger" && "text-danger",
        )}
      >
        {value}
      </p>
      <p className="text-[11px] text-foreground-dim">{hint}</p>
    </div>
  );
}

function QuickAction({
  href,
  icon,
  well,
  title,
  description,
}: {
  href: string;
  icon: ReactNode;
  well: string;
  title: string;
  description: string;
}) {
  return (
    <Link href={href} className="group">
      <Card className="h-full transition-colors group-hover:border-accent/30">
        <div className="flex items-start justify-between">
          <div className={cn("flex h-9 w-9 items-center justify-center rounded-xl", well)}>{icon}</div>
          <IconArrowRight className="h-4 w-4 text-foreground-dim opacity-0 transition-opacity group-hover:opacity-100" />
        </div>
        <p className="mt-4 text-sm font-medium">{title}</p>
        <p className="mt-1 text-sm leading-relaxed text-foreground-dim">{description}</p>
      </Card>
    </Link>
  );
}

function VoiceMark({ name }: { name: string }) {
  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-[11px] font-semibold text-accent-hover">
      {initials || "V"}
    </div>
  );
}
