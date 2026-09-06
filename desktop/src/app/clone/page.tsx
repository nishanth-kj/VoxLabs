"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { api } from "@/lib/api";
import { IconFileAudio, IconMic, IconSparkles, IconUpload } from "@/components/icons";
import {
  Banner,
  Card,
  Input,
  Label,
  Page,
  SectionHeader,
  Segmented,
  SpinnerButton,
  Textarea,
  cn,
} from "@/components/ui";

type Tab = "upload" | "design";

export default function ClonePage() {
  const [tab, setTab] = useState<Tab>("upload");

  return (
    <Page width="narrow">
      <SectionHeader
        kicker="New voice"
        title="Clone voice"
        subtitle="Register a new voice from a consented audio sample, or design one from a text prompt."
      />

      <Segmented
        value={tab}
        onChange={setTab}
        options={[
          { value: "upload", label: "From audio", icon: <IconUpload className="h-3.5 w-3.5" /> },
          { value: "design", label: "From prompt", icon: <IconSparkles className="h-3.5 w-3.5" /> },
        ]}
      />

      {tab === "upload" ? <UploadTab /> : <DesignTab />}
    </Page>
  );
}

function UploadTab() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [projectId, setProjectId] = useState("default");
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultId, setResultId] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  function acceptFile(next: File | null) {
    if (!next) return;
    const ok = next.type.startsWith("audio/") || /\.(wav|mp3|ogg|flac|m4a|webm)$/i.test(next.name);
    if (!ok) {
      setError("Choose an audio file (wav, mp3, ogg, flac, m4a).");
      return;
    }
    setError(null);
    setFile(next);
  }

  async function register() {
    if (!name.trim()) return setError("Give this voice a name.");
    if (!file) return setError("Select an audio sample to clone from.");
    if (!consent) return setError("Confirm you have consent before cloning a voice.");

    setBusy(true);
    setError(null);
    setResultId(null);
    try {
      const result = await api.registerVoice({ name: name.trim(), consent, projectId, audio: file });
      setResultId(result.voice_id);
      setName("");
      setFile(null);
      setConsent(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="flex flex-col gap-4">
      {error && (
        <Banner tone="error" onDismiss={() => setError(null)}>
          {error}
        </Banner>
      )}
      {resultId && (
        <Banner tone="success" onDismiss={() => setResultId(null)}>
          Voice registered.{" "}
          <Link href="/library" className="underline underline-offset-2">
            Open library
          </Link>{" "}
          or{" "}
          <Link href="/studio" className="underline underline-offset-2">
            open studio
          </Link>
          . ID {resultId}
        </Banner>
      )}

      <div>
        <Label htmlFor="voice-name">Voice name</Label>
        <Input
          id="voice-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Narrator - Warm Male"
        />
      </div>

      <div>
        <Label htmlFor="project-id">Project</Label>
        <Input id="project-id" value={projectId} onChange={(e) => setProjectId(e.target.value)} />
      </div>

      <div>
        <Label>Audio sample</Label>
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            acceptFile(e.dataTransfer.files[0] ?? null);
          }}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed px-4 py-8 text-center transition-colors",
            dragOver ? "border-accent bg-accent-soft" : "border-border bg-surface-alt/50 hover:border-[#2e2e3c]",
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            onChange={(e) => acceptFile(e.target.files?.[0] ?? null)}
            className="hidden"
          />
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-surface text-foreground-dim">
            {file ? <IconFileAudio className="h-5 w-5" /> : <IconMic className="h-5 w-5" />}
          </div>
          {file ? (
            <>
              <p className="text-sm font-medium">{file.name}</p>
              <p className="mt-0.5 text-xs text-foreground-dim">{formatBytes(file.size)} · click to replace</p>
            </>
          ) : (
            <>
              <p className="text-sm font-medium">Drop an audio sample here</p>
              <p className="mt-0.5 text-xs text-foreground-dim">or click to browse · wav, mp3, ogg, flac</p>
            </>
          )}
        </div>
      </div>

      <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border bg-surface-alt/40 px-3.5 py-3">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => setConsent(e.target.checked)}
          className="mt-0.5 h-4 w-4 rounded border-border accent-[#6366f1]"
        />
        <span>
          <span className="block text-sm">I have explicit consent from the speaker to clone this voice.</span>
          <span className="mt-0.5 block text-xs text-foreground-dim">
            Required. VoxLabs will not register a voice without this confirmation.
          </span>
        </span>
      </label>

      <SpinnerButton variant="primary" onClick={register} busy={busy} className="self-start">
        {busy ? "Registering…" : "Register voice"}
      </SpinnerButton>
    </Card>
  );
}

function DesignTab() {
  const [projectId, setProjectId] = useState("default");
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultId, setResultId] = useState<string | null>(null);

  async function design() {
    if (!prompt.trim()) return setError("Describe the voice you want to design.");
    setBusy(true);
    setError(null);
    setResultId(null);
    try {
      const result = await api.designVoice(prompt.trim(), projectId);
      setResultId(result.voice_id);
      setPrompt("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="flex flex-col gap-4">
      {error && (
        <Banner tone="error" onDismiss={() => setError(null)}>
          {error}
        </Banner>
      )}
      {resultId && (
        <Banner tone="success" onDismiss={() => setResultId(null)}>
          Voice designed.{" "}
          <Link href="/library" className="underline underline-offset-2">
            Open library
          </Link>
          . ID {resultId}
        </Banner>
      )}

      <div>
        <Label htmlFor="design-project">Project</Label>
        <Input id="design-project" value={projectId} onChange={(e) => setProjectId(e.target.value)} />
      </div>

      <div>
        <Label htmlFor="design-prompt">Describe the voice</Label>
        <Textarea
          id="design-prompt"
          rows={5}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g. Calm, deep-voiced older narrator with a slight British accent"
        />
      </div>

      <SpinnerButton variant="primary" onClick={design} busy={busy} className="self-start">
        {busy ? "Designing…" : "Design voice"}
      </SpinnerButton>
    </Card>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
