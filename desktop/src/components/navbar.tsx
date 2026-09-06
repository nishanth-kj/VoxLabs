"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { logFe } from "@/lib/fe-logs";
import { applyTheme, readTheme, type Theme } from "@/lib/theme";
import {
  IconCpu,
  IconHome,
  IconLibrary,
  IconLock,
  IconMic,
  IconMoon,
  IconSettings,
  IconSliders,
  IconSpeech,
  IconSun,
  IconWaveform,
} from "./icons";
import { SettingsModal } from "./settings-modal";
import { cn } from "./ui";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: IconHome },
  { href: "/studio", label: "Studio", icon: IconSliders },
  { href: "/library", label: "Library", icon: IconLibrary },
  { href: "/models", label: "Models", icon: IconCpu },
  { href: "/clone", label: "Clone", icon: IconMic },
  { href: "/tts", label: "Speech", icon: IconSpeech },
];

export function Navbar() {
  const pathname = usePathname();
  const [online, setOnline] = useState<boolean | null>(null);
  const [theme, setTheme] = useState<Theme>(() => readTheme());
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .getStatus()
      .then(() => !cancelled && setOnline(true))
      .catch(() => !cancelled && setOnline(false));
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  function toggleTheme() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
    logFe("info", `Theme set to ${next}`);
  }

  return (
    <>
    <header className="grid h-14 shrink-0 grid-cols-[1fr_auto_1fr] items-center gap-3 border-b border-border bg-surface/80 px-4 backdrop-blur-md min-[1100px]:px-5">
      <Link href="/" className="flex min-w-0 items-center gap-2.5 justify-self-start">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-400 to-violet-600 text-white shadow-md shadow-indigo-500/25">
          <IconWaveform className="h-4 w-4" />
        </div>
        <div className="min-w-0 leading-tight">
          <p className="text-sm font-semibold tracking-tight">VoxLabs</p>
          <p className="text-[10px] text-foreground-dim">Studio</p>
        </div>
      </Link>

      <nav className="flex items-center gap-1 justify-self-center">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "inline-flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm transition-colors min-[1100px]:gap-2 min-[1100px]:px-3",
                active
                  ? "bg-accent-soft font-medium text-foreground"
                  : "text-foreground-dim hover:bg-surface-alt hover:text-foreground",
              )}
            >
              <Icon className={cn("h-4 w-4", active && "text-accent-hover")} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="flex items-center justify-end gap-2 justify-self-end">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-alt px-2 py-1 text-[11px] text-foreground-dim min-[1100px]:px-2.5">
          <IconLock className="h-3 w-3" />
          <span className="hidden min-[1100px]:inline">Local</span>
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-alt px-2 py-1 text-[11px] text-foreground-dim min-[1100px]:px-2.5">
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              online === null ? "bg-foreground-dim" : online ? "bg-success" : "bg-danger",
            )}
          />
          {online === null ? "Checking" : online ? "Connected" : "Offline"}
        </span>
        <button
          type="button"
          onClick={toggleTheme}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-surface-alt text-foreground-dim hover:text-foreground"
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          title={theme === "dark" ? "Light mode" : "Dark mode"}
        >
          {theme === "dark" ? <IconSun className="h-4 w-4" /> : <IconMoon className="h-4 w-4" />}
        </button>
        <button
          type="button"
          onClick={() => setSettingsOpen(true)}
          className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-border bg-surface-alt px-2.5 text-foreground-dim hover:text-foreground"
          aria-label="Settings"
          title="Settings"
        >
          <IconSettings className="h-4 w-4" />
          <span className="hidden text-xs font-medium min-[1100px]:inline">Settings</span>
        </button>
      </div>
    </header>
    <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}
