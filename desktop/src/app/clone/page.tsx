"use client";

import { useRef, useState } from "react";
import { api } from "@/lib/api";
import { Button, Card, Input, Label, SectionHeader, Textarea } from "@/components/ui";

type Tab = "upload" | "design";

export default function ClonePage() {
  const [tab, setTab] = useState<Tab>("upload");

  return (
    <div className="flex max-w-2xl flex-col gap-5">
      <SectionHeader
        title="Clone Voice"
        subtitle="Register a new voice for cloning, or design one from a text prompt."
      />

      <div className="flex gap-1 border-b border-border">
        {(["upload", "design"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm ${
              tab === t
                ? "border-b-2 border-accent font-semibold text-foreground"
                : "text-foreground-dim hover:text-foreground"
            }`}
          >
            {t === "upload" ? "From Audio Sample" : "Design from Prompt"}
          </button>
        ))}
      </div>

      {tab === "upload" ? <UploadTab /> : <DesignTab />}
    </div>
  );
}

function UploadTab() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [projectId, setProjectId] = useState("default");
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function register() {
    if (!name.trim()) return alert("Give this voice a name.");
    if (!file) return alert("Select an audio sample to clone from.");
    if (!consent) return alert("Confirm you have consent before cloning a voice.");

    setBusy(true);
    try {
      const result = await api.registerVoice({ name: name.trim(), consent, projectId, audio: file });
      alert(`Voice registered with ID ${result.voice_id}`);
      setName("");
      setFile(null);
      setConsent(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="flex flex-col gap-3">
      <div>
        <Label>Voice name</Label>
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Narrator - Warm Male"
        />
      </div>

      <div>
        <Label>Project</Label>
        <Input value={projectId} onChange={(e) => setProjectId(e.target.value)} />
      </div>

      <div>
        <Label>Audio sample</Label>
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full text-sm text-foreground-dim file:mr-3 file:rounded-md file:border file:border-border file:bg-surface-alt file:px-3 file:py-1.5 file:text-foreground"
        />
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        I have explicit consent from the speaker to clone this voice.
      </label>

      <Button variant="primary" onClick={register} disabled={busy}>
        {busy ? "Registering…" : "Register Voice"}
      </Button>
    </Card>
  );
}

function DesignTab() {
  const [projectId, setProjectId] = useState("default");
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);

  async function design() {
    if (!prompt.trim()) return alert("Describe the voice you want to design.");
    setBusy(true);
    try {
      const result = await api.designVoice(prompt.trim(), projectId);
      alert(`Voice designed with ID ${result.voice_id}`);
      setPrompt("");
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="flex flex-col gap-3">
      <div>
        <Label>Project</Label>
        <Input value={projectId} onChange={(e) => setProjectId(e.target.value)} />
      </div>

      <div>
        <Label>Describe the voice you want</Label>
        <Textarea
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g. Calm, deep-voiced older narrator with a slight British accent"
        />
      </div>

      <Button variant="primary" onClick={design} disabled={busy}>
        {busy ? "Designing…" : "Design Voice"}
      </Button>
    </Card>
  );
}
