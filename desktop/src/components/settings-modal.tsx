"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { logFe } from "@/lib/fe-logs";
import { applyTheme, readTheme, type Theme } from "@/lib/theme";
import { IconLock, IconMoon, IconSettings, IconSun, IconX } from "./icons";
import { Badge, Button, Label, Segmented, cn } from "./ui";

type Section = "appearance" | "backend" | "privacy";

const SECTIONS: { id: Section; label: string; hint: string }[] = [
  { id: "appearance", label: "Appearance", hint: "Theme" },
  { id: "backend", label: "Backend", hint: "API connection" },
  { id: "privacy", label: "Privacy", hint: "Local & consent" },
];

export function SettingsModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [section, setSection] = useState<Section>("appearance");
  const [theme, setTheme] = useState<Theme>(() => readTheme());
  const [online, setOnline] = useState<boolean | null>(null);
  const [version, setVersion] = useState<string>("—");
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    api
      .getStatus()
      .then((data) => {
        if (cancelled) return;
        setOnline(true);
        setVersion(data.version);
      })
      .catch(() => {
        if (!cancelled) setOnline(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  if (!open) return null;

  function changeTheme(next: Theme) {
    setTheme(next);
    applyTheme(next);
    logFe("info", `Theme set to ${next}`);
  }

  async function testConnection() {
    setTesting(true);
    try {
      const data = await api.getStatus();
      setOnline(true);
      setVersion(data.version);
      logFe("info", "Settings: backend connection ok");
    } catch (e) {
      setOnline(false);
      logFe("error", `Settings: backend test failed: ${(e as Error).message}`);
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/50 backdrop-blur-[2px]"
        aria-label="Close settings"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
        className="relative z-10 flex h-[min(440px,80vh)] w-full max-w-2xl overflow-hidden rounded-2xl border border-border bg-surface shadow-2xl shadow-black/40"
      >
        <aside className="flex w-48 shrink-0 flex-col border-r border-border bg-surface-alt/40 p-3">
          <div className="mb-3 flex items-center gap-2 px-2 pt-1">
            <IconSettings className="h-4 w-4 text-accent-hover" />
            <h2 id="settings-title" className="text-sm font-semibold tracking-tight">
              Settings
            </h2>
          </div>
          <nav className="flex flex-col gap-0.5">
            {SECTIONS.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setSection(item.id)}
                className={cn(
                  "rounded-lg px-2.5 py-2 text-left",
                  section === item.id
                    ? "bg-accent-soft text-foreground"
                    : "text-foreground-dim hover:bg-surface hover:text-foreground",
                )}
              >
                <span className="block text-sm font-medium">{item.label}</span>
                <span className="block text-[11px] text-foreground-dim">{item.hint}</span>
              </button>
            ))}
          </nav>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex items-center justify-end border-b border-border px-3 py-2">
            <button
              type="button"
              onClick={onClose}
              className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-foreground-dim hover:bg-surface-alt hover:text-foreground"
              aria-label="Close"
            >
              <IconX className="h-4 w-4" />
            </button>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-5">
            {section === "appearance" && (
              <div className="flex flex-col gap-3">
                <div>
                  <h3 className="text-sm font-medium">Appearance</h3>
                  <p className="mt-0.5 text-xs text-foreground-dim">Choose how Studio looks on this machine.</p>
                </div>
                <Label>Theme</Label>
                <Segmented
                  value={theme}
                  onChange={changeTheme}
                  options={[
                    { value: "dark", label: "Dark", icon: <IconMoon className="h-3.5 w-3.5" /> },
                    { value: "light", label: "Light", icon: <IconSun className="h-3.5 w-3.5" /> },
                  ]}
                />
              </div>
            )}

            {section === "backend" && (
              <div className="flex flex-col gap-3">
                <div>
                  <h3 className="text-sm font-medium">Backend</h3>
                  <p className="mt-0.5 text-xs text-foreground-dim">Studio talks to the local FastAPI server.</p>
                </div>
                <Label>API URL</Label>
                <p className="rounded-lg border border-border bg-surface-alt px-3 py-2 font-mono text-xs">{api.baseUrl}</p>
                <div className="flex items-center justify-between gap-3">
                  <Badge tone={online === false ? "danger" : online ? "success" : "neutral"}>
                    {online === null ? "Checking" : online ? `Connected · ${version}` : "Offline"}
                  </Badge>
                  <Button size="sm" onClick={testConnection} disabled={testing}>
                    {testing ? "Testing…" : "Test connection"}
                  </Button>
                </div>
                <p className="text-xs text-foreground-dim">
                  Default is http://127.0.0.1:8000. Start the API if this is offline.
                </p>
              </div>
            )}

            {section === "privacy" && (
              <div className="flex flex-col gap-3">
                <div>
                  <h3 className="text-sm font-medium">Privacy</h3>
                  <p className="mt-0.5 text-xs text-foreground-dim">These guarantees stay on. They cannot be turned off.</p>
                </div>
                <div className="rounded-xl border border-border bg-surface-alt/50 px-3.5 py-3">
                  <p className="flex items-center gap-1.5 text-xs font-medium">
                    <IconLock className="h-3.5 w-3.5 text-success" />
                    Local processing
                  </p>
                  <p className="mt-1 text-xs leading-relaxed text-foreground-dim">
                    Voice samples stay on this machine. Nothing is uploaded to a third-party service.
                  </p>
                </div>
                <div className="rounded-xl border border-border bg-surface-alt/50 px-3.5 py-3">
                  <p className="text-xs font-medium">Consent required</p>
                  <p className="mt-1 text-xs leading-relaxed text-foreground-dim">
                    Cloning a real voice still needs explicit speaker consent before registration.
                  </p>
                </div>
                <div className="rounded-xl border border-border bg-surface-alt/50 px-3.5 py-3">
                  <p className="text-xs font-medium">AI-generated label</p>
                  <p className="mt-1 text-xs leading-relaxed text-foreground-dim">
                    Generated speech is always labeled as AI-generated in Studio.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
