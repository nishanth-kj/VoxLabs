"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "🏠" },
  { href: "/library", label: "Voice Library", icon: "🎙️" },
  { href: "/clone", label: "Clone Voice", icon: "🧬" },
  { href: "/tts", label: "Text to Speech", icon: "🗣️" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [online, setOnline] = useState<boolean | null>(null);

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

  return (
    <aside className="flex w-[200px] shrink-0 flex-col border-r border-border bg-surface">
      <div className="px-4 pt-5 pb-2 text-[17px] font-semibold">VoxLabs</div>

      <nav className="mt-2 flex flex-col">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`px-4 py-2.5 text-sm border-l-[3px] transition-colors ${
                active
                  ? "border-accent bg-surface-alt text-foreground font-semibold"
                  : "border-transparent text-foreground-dim hover:bg-surface-alt hover:text-foreground"
              }`}
            >
              <span className="mr-2">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto p-4">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-alt px-2.5 py-1 text-xs text-foreground-dim">
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              online === null ? "bg-foreground-dim" : online ? "bg-success" : "bg-danger"
            }`}
          />
          {online === null ? "Checking backend…" : online ? "Backend connected" : "Backend offline"}
        </span>
      </div>
    </aside>
  );
}
