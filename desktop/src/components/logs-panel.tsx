"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { api, type BackendLog } from "@/lib/api";
import {
  clearFeLogs,
  getFeLogs,
  logFe,
  subscribeFeLogs,
  type LogEntry,
  type LogLevel,
  type LogSource,
} from "@/lib/fe-logs";
import { IconChevronDown, IconChevronUp, IconTerminal } from "./icons";
import { cn } from "./ui";

type Tab = "all" | "fe" | "be";

function mapLevel(raw: string): LogLevel {
  if (raw === "warning" || raw === "warn") return "warn";
  if (raw === "error" || raw === "critical") return "error";
  if (raw === "debug") return "debug";
  return "info";
}

function fromBackend(row: BackendLog): LogEntry {
  return {
    id: `be-${row.ts}-${row.message}`,
    ts: row.ts,
    source: "be",
    level: mapLevel(row.level),
    message: row.message,
    logger: row.logger,
  };
}

function formatTime(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

const LEVEL_CLASS: Record<LogLevel, string> = {
  debug: "text-foreground-dim",
  info: "text-accent-hover",
  warn: "text-amber-500",
  error: "text-danger",
};

export function LogsPanel() {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("all");
  const [fe, setFe] = useState<LogEntry[]>(() => getFeLogs());
  const [be, setBe] = useState<LogEntry[]>([]);
  const scroller = useRef<HTMLDivElement>(null);
  const stick = useRef(true);

  useEffect(() => subscribeFeLogs(() => setFe(getFeLogs())), []);

  useEffect(() => {
    let cancelled = false;

    async function pull() {
      try {
        const data = await api.getLogs(200);
        if (!cancelled) setBe(data.logs.map(fromBackend));
      } catch {
        /* panel shows FE errors from the failed request */
      }
    }

    void pull();
    const id = window.setInterval(pull, 2500);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  useEffect(() => {
    const onError = (event: ErrorEvent) => {
      logFe("error", event.message || "Unhandled error");
    };
    const onReject = (event: PromiseRejectionEvent) => {
      logFe("error", `Unhandled rejection: ${String(event.reason)}`);
    };
    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onReject);
    return () => {
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onReject);
    };
  }, []);

  const rows = useMemo(() => {
    const merged = tab === "fe" ? fe : tab === "be" ? be : [...fe, ...be];
    return merged.sort((a, b) => a.ts.localeCompare(b.ts));
  }, [tab, fe, be]);

  useEffect(() => {
    if (!open || !stick.current) return;
    const el = scroller.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [rows, open]);

  function sourceLabel(source: LogSource) {
    return source === "fe" ? "FE" : "BE";
  }

  return (
    <section className="shrink-0 border-t border-border bg-surface/90">
      <div className="flex h-9 items-center gap-3 px-4">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="inline-flex items-center gap-2 text-xs font-medium text-foreground"
        >
          <IconTerminal className="h-3.5 w-3.5 text-foreground-dim" />
          Logs
          {open ? <IconChevronDown className="h-3.5 w-3.5 text-foreground-dim" /> : <IconChevronUp className="h-3.5 w-3.5 text-foreground-dim" />}
        </button>

        <div className="flex items-center gap-1">
          {(["all", "fe", "be"] as Tab[]).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setTab(item)}
              className={cn(
                "rounded-md px-2 py-0.5 text-[11px] uppercase tracking-wide",
                tab === item ? "bg-accent-soft text-foreground" : "text-foreground-dim hover:text-foreground",
              )}
            >
              {item === "all" ? "All" : item === "fe" ? "Frontend" : "Backend"}
            </button>
          ))}
        </div>

        <span className="text-[11px] text-foreground-dim">{rows.length} entries</span>

        <button
          type="button"
          onClick={() => {
            clearFeLogs();
            setBe([]);
          }}
          className="ml-auto text-[11px] text-foreground-dim hover:text-foreground"
        >
          Clear
        </button>
      </div>

      {open && (
        <div
          ref={scroller}
          onScroll={(e) => {
            const el = e.currentTarget;
            stick.current = el.scrollHeight - el.scrollTop - el.clientHeight < 24;
          }}
          className="h-40 overflow-auto border-t border-border bg-background/60 px-4 py-2 font-mono text-[11px] leading-5"
        >
          {rows.length === 0 && <p className="text-foreground-dim">No logs yet.</p>}
          {rows.map((row) => (
            <div key={row.id} className="flex gap-3">
              <span className="shrink-0 text-foreground-dim">{formatTime(row.ts)}</span>
              <span className={cn("w-6 shrink-0 font-semibold", row.source === "fe" ? "text-violet-400" : "text-sky-500")}>
                {sourceLabel(row.source)}
              </span>
              <span className={cn("w-12 shrink-0 uppercase", LEVEL_CLASS[row.level])}>{row.level}</span>
              <span className="min-w-0 break-all text-foreground">{row.message}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
