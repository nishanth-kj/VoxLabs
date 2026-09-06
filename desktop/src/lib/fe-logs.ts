export type LogLevel = "debug" | "info" | "warn" | "error";
export type LogSource = "fe" | "be";

export interface LogEntry {
  id: string;
  ts: string;
  source: LogSource;
  level: LogLevel;
  message: string;
  logger?: string;
}

const MAX = 400;
const entries: LogEntry[] = [];
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((fn) => fn());
}

export function pushLog(partial: Omit<LogEntry, "id" | "ts"> & { ts?: string }) {
  const entry: LogEntry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    ts: partial.ts ?? new Date().toISOString(),
    source: partial.source,
    level: partial.level,
    message: partial.message,
    logger: partial.logger,
  };
  entries.push(entry);
  if (entries.length > MAX) entries.splice(0, entries.length - MAX);
  emit();
  return entry;
}

export function getFeLogs(): LogEntry[] {
  return entries.slice();
}

export function clearFeLogs() {
  entries.length = 0;
  emit();
}

export function subscribeFeLogs(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function logFe(level: LogLevel, message: string) {
  pushLog({ source: "fe", level, message, logger: "studio" });
}
