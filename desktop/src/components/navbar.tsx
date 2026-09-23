"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { logFe } from "@/lib/fe-logs";
import { applyTheme, readTheme, type Theme } from "@/lib/theme";
import { IconLibrary, IconMoon, IconSettings, IconSun, IconWaveform } from "./icons";
import { SettingsModal } from "./settings-modal";
import { cn } from "./ui";

const NAV_ITEMS = [
  { href: "/", label: "Home" },
  { href: "/studio", label: "Studio" },
  { href: "/clone", label: "Clone" },
  { href: "/library", label: "Library", icon: IconLibrary },
  { href: "/models", label: "Models" },
  { href: "/tts", label: "Quick TTS" },
];

export function Navbar() {
  const pathname = usePathname();
  const [online, setOnline] = useState<boolean | null>(null);
  const [theme, setTheme] = useState<Theme>(() => readTheme());
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.getStatus()
      .then(() => !cancelled && setOnline(true))
      .catch(() => !cancelled && setOnline(false));
    return () => { cancelled = true; };
  }, [pathname]);

  useEffect(() => {
    const open = () => setSettingsOpen(true);
    window.addEventListener("voxlabs:settings", open);
    return () => window.removeEventListener("voxlabs:settings", open);
  }, []);

  function toggleTheme() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
    logFe("info", `Theme set to ${next}`);
  }

  return (
    <>
      <header className="sticky top-0 z-40 shrink-0 border-b border-border bg-surface/85 backdrop-blur-xl">
        <div className="mx-auto flex h-14 w-full items-center gap-3 px-4 sm:px-6">
          <Link href="/" className="flex min-w-0 items-center gap-2.5">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-400 to-violet-600 text-white shadow-md shadow-indigo-500/20">
              <IconWaveform className="h-4 w-4" />
            </div>
            <div className="hidden leading-tight sm:block">
              <p className="text-sm font-semibold tracking-tight">VoxLabs</p>
              <p className="text-[10px] text-foreground-dim">Voice Studio</p>
            </div>
          </Link>

          <nav className="ml-2 flex min-w-0 flex-1 items-center gap-1 overflow-x-auto">
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "inline-flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs transition-colors sm:text-sm",
                    active
                      ? "bg-accent-soft font-medium text-foreground"
                      : "text-foreground-dim hover:bg-surface-alt hover:text-foreground",
                  )}
                >
                  {Icon && <Icon className={cn("h-3.5 w-3.5", active && "text-accent-hover")} />}
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="flex shrink-0 items-center gap-1.5">
            <span className="hidden items-center gap-1.5 rounded-full border border-border bg-surface-alt px-2.5 py-1 text-[11px] text-foreground-dim sm:inline-flex">
              <span className={cn("h-1.5 w-1.5 rounded-full", online === null ? "bg-foreground-dim" : online ? "bg-success" : "bg-danger")} />
              {online === null ? "Checking" : online ? "Connected" : "Offline"}
            </span>
            <button
              type="button"
              onClick={toggleTheme}
              className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface-alt text-foreground-dim hover:text-foreground"
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? <IconSun className="h-4 w-4" /> : <IconMoon className="h-4 w-4" />}
            </button>
            <button
              type="button"
              onClick={() => setSettingsOpen(true)}
              className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface-alt text-foreground-dim hover:text-foreground"
              aria-label="Settings"
            >
              <IconSettings className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}
