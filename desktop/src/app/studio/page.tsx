"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api, EdgeVoice, Voice } from "@/lib/api";
import { AudioPlayer } from "@/components/audio-player";
import { IconMic, IconPlus, IconSearch, IconSpeech } from "@/components/icons";
import {
  Badge,
  Banner,
  Button,
  Label,
  Segmented,
  Select,
  Slider,
  SpinnerButton,
  Textarea,
  WaveformBars,
  buttonStyles,
  cn,
} from "@/components/ui";

const FALLBACK_EMOTIONS = ["neutral", "happy", "sad", "angry"];

type Engine = "emotional" | "edge";

type Take = {
  id: string;
  url: string;
  text: string;
  voice: string;
  emotion: string;
  at: string;
};

export default function StudioPage() {
  const [text, setText] = useState("");
  const [engine, setEngine] = useState<Engine>("emotional");
  const [query, setQuery] = useState("");

  const [voices, setVoices] = useState<Voice[]>([]);
  const [voiceId, setVoiceId] = useState("");
  const [emotions, setEmotions] = useState<string[]>(FALLBACK_EMOTIONS);
  const [emotion, setEmotion] = useState("neutral");
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);
  const [energy, setEnergy] = useState(1.0);

  const [edgeVoices, setEdgeVoices] = useState<EdgeVoice[]>([]);
  const [edgeVoice, setEdgeVoice] = useState("");
  const [edgeRate, setEdgeRate] = useState(0);
  const [edgePitch, setEdgePitch] = useState(0);
  const [edgeVolume, setEdgeVolume] = useState(0);

  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Write a line, then generate.");
  const [error, setError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [takes, setTakes] = useState<Take[]>([]);

  useEffect(() => {
    let cancelled = false;
    api
      .listVoices()
      .then((data) => {
        if (!cancelled) setVoices(data.voices);
      })
      .catch(() => {});
    api
      .listEdgeVoices()
      .then((list) => {
        if (cancelled) return;
        setEdgeVoices(list);
        if (list[0]) setEdgeVoice(list[0].ShortName);
      })
      .catch(() => {});
    api
      .getEmotions()
      .then((data) => {
        const names = Object.keys(data.emotions ?? {});
        if (!cancelled && names.length) setEmotions(names);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredLocal = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return voices;
    return voices.filter((v) => `${v.name} ${v.voice_id}`.toLowerCase().includes(q));
  }, [voices, query]);

  const filteredEdge = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = q
      ? edgeVoices.filter((v) => `${v.ShortName} ${String(v.FriendlyName ?? "")}`.toLowerCase().includes(q))
      : edgeVoices;
    return list.slice(0, 40);
  }, [edgeVoices, query]);

  const selectedVoiceLabel =
    engine === "edge"
      ? edgeVoice || "Edge voice"
      : voices.find((v) => v.voice_id === voiceId)?.name || "Default synthetic";

  async function generate() {
    if (!text.trim()) return setError("Type something to synthesize.");
    setBusy(true);
    setError(null);
    setStatus("Generating audio…");
    try {
      let result;
      if (engine === "edge") {
        if (!edgeVoice) throw new Error("No Edge voice available yet.");
        result = await api.generateEdgeSpeech({
          text,
          voice: edgeVoice,
          rate: `${edgeRate >= 0 ? "+" : ""}${edgeRate}%`,
          pitch: `${edgePitch >= 0 ? "+" : ""}${edgePitch}Hz`,
          volume: `${edgeVolume >= 0 ? "+" : ""}${edgeVolume}%`,
        });
      } else {
        result = await api.textToSpeech({
          text,
          engine: "emotional",
          voiceId: voiceId || undefined,
          language: "en",
          emotion,
          speed,
          pitch,
          energy,
        });
      }
      const url = api.audioUrl(result.audio_url);
      setAudioUrl(url);
      setStatus("Ready to play.");
      setTakes((prev) =>
        [
          {
            id: `${Date.now()}`,
            url,
            text: text.trim(),
            voice: selectedVoiceLabel,
            emotion: engine === "edge" ? "edge" : emotion,
            at: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
          ...prev,
        ].slice(0, 12),
      );
    } catch (e) {
      setStatus("Generation failed.");
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-0 flex-1 overflow-hidden">
      <aside className="flex w-[200px] shrink-0 flex-col border-r border-border bg-surface/70 min-[1200px]:w-56">
        <div className="border-b border-border px-3 py-3">
          <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-foreground-dim">Voices</p>
          <div className="relative mt-2">
            <IconSearch className="pointer-events-none absolute top-1/2 left-2.5 h-3.5 w-3.5 -translate-y-1/2 text-foreground-dim" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search"
              className="h-8 w-full rounded-lg border border-border bg-surface-alt pr-2 pl-8 text-xs outline-none focus:border-accent"
            />
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
          <p className="px-2 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-foreground-dim">Local</p>
          <button
            type="button"
            onClick={() => {
              setEngine("emotional");
              setVoiceId("");
            }}
            className={cn(
              "mb-0.5 flex w-full items-center rounded-lg px-2.5 py-2 text-left text-sm",
              engine === "emotional" && !voiceId
                ? "bg-accent-soft text-foreground"
                : "text-foreground-dim hover:bg-surface-alt hover:text-foreground",
            )}
          >
            Default synthetic
          </button>
          {filteredLocal.map((voice) => (
            <button
              key={voice.voice_id}
              type="button"
              onClick={() => {
                setEngine("emotional");
                setVoiceId(voice.voice_id);
              }}
              className={cn(
                "mb-0.5 flex w-full items-center rounded-lg px-2.5 py-2 text-left text-sm",
                engine === "emotional" && voiceId === voice.voice_id
                  ? "bg-accent-soft text-foreground"
                  : "text-foreground-dim hover:bg-surface-alt hover:text-foreground",
              )}
            >
              <span className="truncate">{voice.name}</span>
            </button>
          ))}
          {voices.length === 0 && (
            <p className="px-2.5 py-2 text-xs text-foreground-dim">No cloned voices yet.</p>
          )}

          <p className="mt-3 px-2 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-foreground-dim">
            Edge
          </p>
          {filteredEdge.map((voice) => (
            <button
              key={voice.ShortName}
              type="button"
              onClick={() => {
                setEngine("edge");
                setEdgeVoice(voice.ShortName);
              }}
              className={cn(
                "mb-0.5 flex w-full items-center rounded-lg px-2.5 py-2 text-left text-sm",
                engine === "edge" && edgeVoice === voice.ShortName
                  ? "bg-accent-soft text-foreground"
                  : "text-foreground-dim hover:bg-surface-alt hover:text-foreground",
              )}
            >
              <span className="truncate">{voice.ShortName}</span>
            </button>
          ))}
          {edgeVoices.length === 0 && (
            <p className="px-2.5 py-2 text-xs text-foreground-dim">Edge catalog unavailable.</p>
          )}
        </div>

        <div className="border-t border-border p-3">
          <Link href="/clone" className={buttonStyles("default", "sm", "w-full")}>
            <IconPlus className="h-3.5 w-3.5" />
            Clone a voice
          </Link>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-3">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-foreground-dim">Session</p>
            <h1 className="text-lg font-semibold tracking-tight">Studio</h1>
          </div>
          <div className="flex items-center gap-2">
            <Segmented
              value={engine}
              onChange={setEngine}
              options={[
                { value: "emotional", label: "Emotional" },
                { value: "edge", label: "Edge" },
              ]}
            />
            <Badge>Local processing</Badge>
          </div>
        </div>

        <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_220px] min-[1200px]:grid-cols-[minmax(0,1fr)_260px]">
          <section className="flex min-h-0 flex-col gap-3 overflow-hidden p-5">
            {error && (
              <Banner tone="error" onDismiss={() => setError(null)}>
                {error}
              </Banner>
            )}
            <div className="flex items-center justify-between">
              <Label htmlFor="studio-script">Script</Label>
              <span className="text-[11px] text-foreground-dim">{text.length} characters</span>
            </div>
            <Textarea
              id="studio-script"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Hello - this is my cloned voice, generated on this computer."
              className="min-h-0 flex-1 resize-none text-base leading-relaxed"
            />
            <div className="flex flex-wrap items-center gap-2">
              {engine === "emotional" &&
                emotions.slice(0, 8).map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setEmotion(item)}
                    className={cn(
                      "rounded-full border px-3 py-1 text-xs capitalize",
                      emotion === item
                        ? "border-accent/40 bg-accent-soft text-foreground"
                        : "border-border text-foreground-dim hover:text-foreground",
                    )}
                  >
                    {item}
                  </button>
                ))}
              {engine === "emotional" && (
                <>
                  <span className="rounded-full border border-border px-3 py-1 text-xs text-foreground-dim">
                    Pitch {pitch.toFixed(2)}
                  </span>
                  <span className="rounded-full border border-border px-3 py-1 text-xs text-foreground-dim">
                    Speed {speed.toFixed(2)}
                  </span>
                </>
              )}
              <Badge tone="success">AI-generated</Badge>
            </div>
            <SpinnerButton variant="primary" onClick={generate} busy={busy} className="self-start">
              {busy ? "Generating…" : "Generate take"}
            </SpinnerButton>
          </section>

          <aside className="flex min-h-0 flex-col gap-4 overflow-hidden border-l border-border p-5">
            <div>
              <h2 className="text-sm font-medium">Delivery</h2>
              <p className="mt-0.5 text-xs text-foreground-dim">{selectedVoiceLabel}</p>
            </div>

            {engine === "emotional" ? (
              <>
                <div>
                  <Label htmlFor="studio-voice">Voice</Label>
                  <Select id="studio-voice" value={voiceId} onChange={(e) => setVoiceId(e.target.value)}>
                    <option value="">Default synthetic voice</option>
                    {voices.map((v) => (
                      <option key={v.voice_id} value={v.voice_id}>
                        {v.name}
                      </option>
                    ))}
                  </Select>
                </div>
                <Slider label="Speed" value={speed} onChange={setSpeed} min={0.5} max={2} />
                <Slider label="Pitch" value={pitch} onChange={setPitch} min={0.5} max={2} />
                <Slider label="Energy" value={energy} onChange={setEnergy} min={0.5} max={2} />
              </>
            ) : (
              <>
                <div>
                  <Label htmlFor="studio-edge">Edge voice</Label>
                  <Select id="studio-edge" value={edgeVoice} onChange={(e) => setEdgeVoice(e.target.value)}>
                    {edgeVoices.map((v) => (
                      <option key={v.ShortName} value={v.ShortName}>
                        {v.ShortName}
                      </option>
                    ))}
                  </Select>
                </div>
                <Slider
                  label="Rate"
                  value={edgeRate}
                  onChange={setEdgeRate}
                  min={-50}
                  max={100}
                  step={1}
                  format={(v) => `${v}%`}
                />
                <Slider
                  label="Pitch offset"
                  value={edgePitch}
                  onChange={setEdgePitch}
                  min={-50}
                  max={50}
                  step={1}
                  format={(v) => `${v} Hz`}
                />
                <Slider
                  label="Volume"
                  value={edgeVolume}
                  onChange={setEdgeVolume}
                  min={-50}
                  max={100}
                  step={1}
                  format={(v) => `${v}%`}
                />
              </>
            )}

            <div className="mt-auto rounded-xl border border-border bg-surface-alt/50 px-3 py-3">
              <p className="flex items-center gap-1.5 text-xs font-medium">
                <IconMic className="h-3.5 w-3.5 text-success" />
                Consent stays required
              </p>
              <p className="mt-1 text-xs leading-relaxed text-foreground-dim">
                Cloned voices come from the library. Registering a new one still needs explicit speaker consent.
              </p>
            </div>
          </aside>
        </div>

        <section className="border-t border-border bg-surface/80 px-5 py-3">
          <div className="mb-2 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-soft text-accent-hover">
                <IconSpeech className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-medium">Output</p>
                <p className="text-xs text-foreground-dim">{status}</p>
              </div>
            </div>
            <Badge tone="success">AI-generated</Badge>
          </div>
          <WaveformBars active={Boolean(audioUrl)} className="mb-2 h-8" />
          <AudioPlayer key={audioUrl ?? "empty"} src={audioUrl} />
          {takes.length > 0 && (
            <ul className="mt-3 flex gap-2 overflow-x-auto pb-1">
              {takes.map((take) => (
                <li key={take.id}>
                  <Button
                    size="sm"
                    variant={take.url === audioUrl ? "primary" : "default"}
                    onClick={() => {
                      setAudioUrl(take.url);
                      setStatus("Ready to play.");
                    }}
                  >
                    {take.at} · {take.voice}
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
