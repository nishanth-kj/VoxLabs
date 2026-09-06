"use client";

import { useRef, useState } from "react";
import { IconPause, IconPlay } from "./icons";

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function AudioPlayer({ src }: { src: string | null }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);

  function toggle() {
    const el = audioRef.current;
    if (!el || !src) return;
    if (el.paused) {
      void el.play();
    } else {
      el.pause();
    }
  }

  const pct = duration > 0 ? (current / duration) * 100 : 0;

  return (
    <div className="flex items-center gap-3">
      <audio
        ref={audioRef}
        src={src ?? undefined}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onTimeUpdate={(e) => setCurrent(e.currentTarget.currentTime)}
        onLoadedMetadata={(e) => setDuration(e.currentTarget.duration || 0)}
        onEnded={() => setPlaying(false)}
      />
      <button
        type="button"
        onClick={toggle}
        disabled={!src}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent text-white shadow-[0_0_16px_rgba(99,102,241,0.3)] disabled:opacity-40"
        aria-label={playing ? "Pause" : "Play"}
      >
        {playing ? <IconPause className="h-3.5 w-3.5" /> : <IconPlay className="h-3.5 w-3.5" />}
      </button>
      <span className="w-10 shrink-0 font-mono text-[11px] tabular-nums text-foreground-dim">{formatTime(current)}</span>
      <input
        type="range"
        min={0}
        max={duration || 0}
        step={0.01}
        value={current}
        disabled={!src}
        onChange={(e) => {
          const next = Number(e.target.value);
          setCurrent(next);
          if (audioRef.current) audioRef.current.currentTime = next;
        }}
        className="flex-1"
        style={{ background: `linear-gradient(to right, var(--accent) ${pct}%, #2a2a36 ${pct}%)` }}
      />
      <span className="w-10 shrink-0 text-right font-mono text-[11px] tabular-nums text-foreground-dim">
        {formatTime(duration)}
      </span>
    </div>
  );
}
