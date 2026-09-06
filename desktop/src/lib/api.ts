import { logFe } from "./fe-logs";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8942";

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.status = status;
  }
}

interface Envelope<T> {
  status: number;
  data: T | null;
  error: { status?: number; message: string } | string | null;
}

function shortPath(url: string) {
  try {
    const parsed = new URL(url, BASE_URL);
    return parsed.pathname + parsed.search;
  } catch {
    return url;
  }
}

async function request(url: string, init?: RequestInit, timeoutMs?: number): Promise<Response> {
  const method = (init?.method ?? "GET").toUpperCase();
  const path = shortPath(url);
  const silent = path.startsWith("/api/logs");
  const started = performance.now();

  const options: RequestInit = { ...init };
  if (timeoutMs && timeoutMs > 0) {
    options.signal = AbortSignal.timeout(timeoutMs);
  }

  try {
    const res = await fetch(url, options);
    if (!silent) {
      const ms = Math.round(performance.now() - started);
      logFe(res.ok ? "info" : "error", `${method} ${path} ${res.status} (${ms}ms)`);
    }
    return res;
  } catch (err) {
    if (!silent) {
      logFe("error", `${method} ${path} failed: ${(err as Error).message}`);
    }
    throw err;
  }
}

function get(url: string, timeoutMs = 8000) {
  return request(url, undefined, timeoutMs);
}

async function unwrap<T>(res: Response): Promise<T> {
  let payload: Envelope<T>;
  try {
    payload = await res.json();
  } catch {
    if (!res.ok) throw new ApiError(res.statusText, res.status);
    throw new ApiError("Invalid response from server");
  }

  if (!res.ok || payload.status === 0) {
    const err = payload.error;
    const message = typeof err === "string" ? err : err?.message || "Request failed";
    throw new ApiError(message, res.status);
  }

  return payload.data as T;
}

export interface Voice {
  voice_id: string;
  name: string;
  project_id?: string;
  [key: string]: unknown;
}

export interface SystemStatus {
  engine_ready: boolean;
  version: string;
  capabilities: string[];
  memory_optimization: string;
}

export interface EdgeVoice {
  ShortName: string;
  [key: string]: unknown;
}

export interface BackendLog {
  ts: string;
  level: string;
  logger: string;
  message: string;
}

export interface StudioModel {
  id: string;
  name: string;
  kind: "engine" | "voice" | string;
  provider: string;
  status: string;
  offline?: boolean;
  description?: string;
  capabilities?: string[];
  endpoint?: string;
  note?: string | null;
  locale?: string;
  gender?: string;
  engine?: string;
  variant_count?: number;
}

export interface ModelsCatalog {
  models: StudioModel[];
  engines: StudioModel[];
  voices: StudioModel[];
  count: number;
  engine_count: number;
  voice_count: number;
}

export const api = {
  baseUrl: BASE_URL,

  async getStatus(): Promise<SystemStatus> {
    const res = await get(`${BASE_URL}/api/status`);
    return unwrap(res);
  },

  async getEmotions(): Promise<{ emotions: Record<string, unknown> }> {
    const res = await get(`${BASE_URL}/api/emotions`);
    return unwrap(res);
  },

  async getLogs(limit = 200): Promise<{ logs: BackendLog[]; count: number }> {
    const res = await get(`${BASE_URL}/api/logs?limit=${limit}`, 8000);
    return unwrap(res);
  },

  async listModels(): Promise<ModelsCatalog> {
    const res = await get(`${BASE_URL}/api/models`, 20000);
    return unwrap(res);
  },

  async listVoices(projectId?: string): Promise<{ voices: Voice[]; count: number }> {
    const url = new URL(`${BASE_URL}/api/voices`);
    if (projectId) url.searchParams.set("project_id", projectId);
    const res = await get(url.toString());
    return unwrap(res);
  },

  async registerVoice(params: { name: string; consent: boolean; projectId: string; audio: File }): Promise<{ voice_id: string }> {
    const form = new FormData();
    form.set("name", params.name);
    form.set("consent", String(params.consent));
    form.set("project_id", params.projectId);
    form.set("audio", params.audio);
    const res = await request(`${BASE_URL}/api/voices/register`, { method: "POST", body: form });
    return unwrap(res);
  },

  async designVoice(prompt: string, projectId: string): Promise<{ voice_id: string }> {
    const form = new FormData();
    form.set("prompt", prompt);
    form.set("project_id", projectId);
    const res = await request(`${BASE_URL}/api/voices/design`, { method: "POST", body: form });
    return unwrap(res);
  },

  async revokeVoice(voiceId: string): Promise<{ message: string }> {
    const res = await request(`${BASE_URL}/api/voices/${voiceId}`, { method: "DELETE" });
    return unwrap(res);
  },

  voiceSourceUrl(voiceId: string): string {
    return `${BASE_URL}/api/voices/${voiceId}/source`;
  },

  async listEdgeVoices(): Promise<EdgeVoice[]> {
    const res = await get(`${BASE_URL}/api/tts/edge/voices`);
    return unwrap(res);
  },

  async generateEdgeSpeech(params: { text: string; voice: string; rate: string; pitch: string; volume: string }): Promise<{ audio_url: string }> {
    const res = await request(`${BASE_URL}/api/tts/edge/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    return unwrap(res);
  },

  async textToSpeech(params: {
    text: string;
    engine: string;
    voiceId?: string;
    language: string;
    emotion: string;
    speed: number;
    pitch: number;
    energy: number;
  }): Promise<{ audio_url: string }> {
    const form = new FormData();
    form.set("text", params.text);
    form.set("engine", params.engine);
    form.set("language", params.language);
    form.set("emotion", params.emotion);
    form.set("speed", String(params.speed));
    form.set("pitch", String(params.pitch));
    form.set("energy", String(params.energy));
    if (params.voiceId) form.set("voice_id", params.voiceId);
    const res = await request(`${BASE_URL}/api/tts`, { method: "POST", body: form });
    return unwrap(res);
  },

  audioUrl(path: string): string {
    return `${BASE_URL}${path}`;
  },
};
