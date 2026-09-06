"use client";

import { useEffect, useRef, useState } from "react";
import { api, EdgeVoice, Voice } from "@/lib/api";
import { Button, Card, SectionHeader, Select, Slider, Textarea } from "@/components/ui";

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
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

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
    if (!text.trim()) return alert("Type something to synthesize.");
    setBusy(true);
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
      requestAnimationFrame(() => audioRef.current?.play());
    } catch (e) {
      setStatus("Generation failed.");
      alert((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex max-w-2xl flex-col gap-5">
      <SectionHeader
        title="Text to Speech"
        subtitle="Generate speech with the emotional engine or Microsoft Edge voices."
      />

      <Card className="flex flex-col gap-4">
        <Textarea
          rows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type the text you want to synthesize…"
        />

        <div className="flex items-center gap-3">
          <span className="text-sm text-foreground-dim">Engine</span>
          <Select value={engine} onChange={(e) => setEngine(e.target.value as Engine)} className="w-auto">
            <option value="emotional">Emotional (local)</option>
            <option value="edge">Edge (Microsoft)</option>
          </Select>
        </div>

        {engine === "emotional" ? (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <span className="w-16 text-sm text-foreground-dim">Voice</span>
              <Select value={voiceId} onChange={(e) => setVoiceId(e.target.value)}>
                <option value="">Default synthetic voice</option>
                {voices.map((v) => (
                  <option key={v.voice_id} value={v.voice_id}>
                    {v.name} ({v.voice_id.slice(0, 8)})
                  </option>
                ))}
              </Select>
            </div>

            <div className="flex items-center gap-3">
              <span className="w-16 text-sm text-foreground-dim">Emotion</span>
              <Select value={emotion} onChange={(e) => setEmotion(e.target.value)}>
                {EMOTIONS.map((e) => (
                  <option key={e} value={e}>
                    {e}
                  </option>
                ))}
              </Select>
            </div>

            <Slider label="Speed" value={speed} onChange={setSpeed} min={0.5} max={2} />
            <Slider label="Pitch" value={pitch} onChange={setPitch} min={0.5} max={2} />
            <Slider label="Energy" value={energy} onChange={setEnergy} min={0.5} max={2} />
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <span className="w-16 text-sm text-foreground-dim">Voice</span>
              <Select value={edgeVoice} onChange={(e) => setEdgeVoice(e.target.value)}>
                {edgeVoices.map((v) => (
                  <option key={v.ShortName} value={v.ShortName}>
                    {v.ShortName}
                  </option>
                ))}
              </Select>
            </div>

            <Slider
              label="Rate %"
              value={edgeRate}
              onChange={setEdgeRate}
              min={-50}
              max={100}
              step={1}
              format={(v) => `${v}%`}
            />
            <Slider
              label="Pitch (Hz offset)"
              value={edgePitch}
              onChange={setEdgePitch}
              min={-50}
              max={50}
              step={1}
              format={(v) => `${v}Hz`}
            />
            <Slider
              label="Volume %"
              value={edgeVolume}
              onChange={setEdgeVolume}
              min={-50}
              max={100}
              step={1}
              format={(v) => `${v}%`}
            />
          </div>
        )}

        <Button variant="primary" onClick={generate} disabled={busy}>
          {busy ? "Generating…" : "Generate Speech"}
        </Button>

        <div className="flex items-center gap-3">
          <audio ref={audioRef} src={audioUrl ?? undefined} controls className="h-9 flex-1" />
        </div>
        <p className="text-sm text-foreground-dim">{status}</p>
      </Card>
    </div>
  );
}
