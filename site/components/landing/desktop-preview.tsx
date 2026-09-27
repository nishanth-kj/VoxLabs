export function DesktopPreview() {
  const bars = [18, 32, 24, 44, 28, 52, 36, 22, 48, 30, 40, 20, 56, 34, 26, 42, 18, 38, 28, 46]

  return (
    <div className="relative mx-auto w-full max-w-4xl">
      <div className="absolute -inset-4 rounded-3xl bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent blur-2xl pointer-events-none" />
      <div className="relative rounded-xl border border-border/40 bg-card/80 shadow-2xl overflow-hidden backdrop-blur-sm">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border/40 bg-secondary/50">
          <span className="h-2.5 w-2.5 rounded-full bg-red-400/80" />
          <span className="h-2.5 w-2.5 rounded-full bg-yellow-400/80" />
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#6352f0"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="ml-2 h-4 w-4 shrink-0"
            aria-hidden="true"
          >
            <rect x="1" y="1" width="22" height="22" rx="6" fill="#6352f0" stroke="none" />
            <path d="M7 10v4M10 7v10M13 9v6M16 11v2" stroke="#ffffff" strokeWidth="2.2" />
          </svg>
          <span className="text-xs font-medium text-muted-foreground">VoxLabs Studio</span>
          <span className="ml-auto text-[10px] uppercase tracking-wider text-muted-foreground/70">
            Desktop · Local
          </span>
        </div>
        <div className="grid md:grid-cols-[200px_1fr] min-h-[260px]">
          <aside className="hidden md:flex flex-col gap-3 border-r border-border/40 p-4 text-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Voices</p>
            {["Studio Narrator", "My Voice", "Podcast Host"].map((name, i) => (
              <div
                key={name}
                className={`rounded-md px-3 py-2 ${i === 1 ? "bg-indigo-500/15 text-foreground" : "text-muted-foreground"}`}
              >
                {name}
              </div>
            ))}
          </aside>
          <div className="p-6 space-y-5">
            <p className="text-sm text-muted-foreground italic">
              “Hello — this is my cloned voice, generated on this computer.”
            </p>
            <div className="flex items-end gap-1 h-16" aria-hidden>
              {bars.map((h, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-sm bg-gradient-to-t from-indigo-500/80 to-purple-400/70"
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="rounded-full border border-border/50 px-3 py-1">Emotion: Warm</span>
              <span className="rounded-full border border-border/50 px-3 py-1">Pitch 1.0</span>
              <span className="rounded-full border border-border/50 px-3 py-1">Speed 1.0</span>
              <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 px-3 py-1">
                AI-generated
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
