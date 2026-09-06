"use client";

import { useEffect, useState } from "react";
import { api, EdgeVoice, Voice } from "@/lib/api";
import { AudioPlayer } from "@/components/audio-player";
import { IconSpeech } from "@/components/icons";
import {
  Badge,
  Banner,
  Card,
  Label,
  Page,
  SectionHeader,
  Segmented,
  Select,
  Slider,
  SpinnerButton,
  Textarea,
  WaveformBars,
} from "@/components/ui";

const EMOTIONS = ["neutral", "happy", "sad", "angry"];

type Engine = "emotional" | "edge";

export default function TtsPage() {
  const [text, setText] = useState("");
  const [engine, setEngine] = useState<Engine>("emotional");

  const [voices, setVoices] = useState<Voice[]>([]);
  const [voiceId, setVoiceId] = useState<string>("");
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
  const [status, setStatus] = useState("No audio generated yet.");
  const [error, setError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  useEffect(() => {
    api
      .listVoices()
      .then((data) => setVoices(data.voices))
      .catch(() => {});
    api
      .listEdgeVoices()
      .then((list) => {
        setEdgeVoices(list);
        if (list.length) setEdgeVoice(list[0].ShortName);
      })
      .catch(() => {});
  }, []);

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
      setAudioUrl(api.audioUrl(result.audio_url));
      setStatus("Ready to play.");
    } catch (e) {
      setStatus("Generation failed.");
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page>
      <SectionHeader
        kicker="Synthesize"
        title="Text to speech"
        subtitle="Write a script, pick a voice, and generate speech on this machine."
        actions={
          <Segmented
            value={engine}
            onChange={setEngine}
            options={[
              { value: "emotional", label: "Emotional" },
              { value: "edge", label: "Edge" },
            ]}
          />
        }
      />

      {error && (
        <Banner tone="error" onDismiss={() => setError(null)}>
          {error}
        </Banner>
      )}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="script">Script</Label>
            <span className="text-[11px] text-foreground-dim">{text.length} characters</span>
          </div>
          <Textarea
            id="script"
            rows={8}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type the text you want to synthesize…"
            className="min-h-[150px] flex-1"
          />
          <SpinnerButton variant="primary" onClick={generate} busy={busy} className="self-start">
            {busy ? "Generating…" : "Generate speech"}
          </SpinnerButton>
        </Card>

        <Card className="flex flex-col gap-5">
          <div>
            <h2 className="text-sm font-medium">Voice & delivery</h2>
            <p className="mt-0.5 text-xs text-foreground-dim">
              {engine === "emotional" ? "Local emotional engine" : "Microsoft Edge voices"}
            </p>
          </div>

          {engine === "emotional" ? (
            <>
              <div>
                <Label htmlFor="voice">Voice</Label>
                <Select id="voice" value={voiceId} onChange={(e) => setVoiceId(e.target.value)}>
                  <option value="">Default synthetic voice</option>
                  {voices.map((v) => (
                    <option key={v.voice_id} value={v.voice_id}>
                      {v.name}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <Label htmlFor="emotion">Emotion</Label>
                <Select id="emotion" value={emotion} onChange={(e) => setEmotion(e.target.value)}>
                  {EMOTIONS.map((item) => (
                    <option key={item} value={item}>
                      {item}
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
                <Label htmlFor="edge-voice">Voice</Label>
                <Select id="edge-voice" value={edgeVoice} onChange={(e) => setEdgeVoice(e.target.value)}>
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
        </Card>
      </div>

      <Card className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
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

        <WaveformBars active={Boolean(audioUrl)} className="h-8 rounded-lg bg-surface-alt/60 px-3 py-1.5" />
        <AudioPlayer key={audioUrl ?? "empty"} src={audioUrl} />
      </Card>
    </Page>
  );
}
