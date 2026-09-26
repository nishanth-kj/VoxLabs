import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Download,
  Monitor,
  ShieldCheck,
  Mic,
  Cpu,
  Terminal,
  Layers,
  FileText,
  Sliders,
  Database,
  Code2,
  LayoutGrid,
} from "lucide-react"
import Link from "next/link"
import { GITHUB_URL, RELEASES_URL } from "@/lib/links"

const DOC_SECTIONS = [
  { id: "install", label: "1. Installation & Setup" },
  { id: "desktop-ui", label: "2. Desktop Studio & Shortcuts" },
  { id: "architecture", label: "3. Architecture & Flow" },
  { id: "voice-cloning", label: "4. Voice Cloning & Consent" },
  { id: "tts", label: "5. Text to Speech & Engines" },
  { id: "script-to-audio", label: "6. Script & Lesson to Audio" },
  { id: "audio-engine", label: "7. Audio Engine, DSP & Editor" },
  { id: "database", label: "8. Database & Transactions" },
  { id: "rest-api-mcp", label: "9. REST API & MCP Server" },
  { id: "development", label: "10. Development & Extending" },
] as const

const ENV_VARS = [
  { name: "VOXLABS_DATA_DIR", effect: "Where the database, audio, voices, models, cache, and logs live (default ./data)" },
  { name: "VOXLABS_DB_PATH", effect: "Override only the SQLite database file path (default data/database/voxlabs.db)" },
  { name: "VOXLABS_API_TOKEN", effect: "Require a Authorization: Bearer <token> header on the REST API and HTTP MCP server" },
  { name: "LOG_LEVEL", effect: "Initial log level: DEBUG, INFO, WARNING, or ERROR (the Settings page can also change it)" },
] as const

const DESKTOP_PAGES = [
  { page: "Home (Ctrl+1)", desc: "Quick-start workflow cards, recent generated/imported audio library, and one-click navigation into the editor or studio." },
  { page: "Studio (Ctrl+2)", desc: "One script at a glance: section list, voice inspector, multi-take selector, interactive clip timeline over the rendered waveform, and transport controls." },
  { page: "Clone Voice (Ctrl+3)", desc: "Guided workflow: import or record reference samples → automatic quality analysis table → attributed speaker consent form → cloning model picker → preview & save." },
  { page: "Generate Speech (Ctrl+4)", desc: "Single or multi-sentence TTS with voice, built-in engine_voice, model, emotion, style, speed, pitch, energy, temperature, seed, inline pauses, pronunciations, and sentence regeneration." },
  { page: "Script to Audio (Ctrl+5)", desc: "Plain-text script & lesson editor (autosaves after 0.8 s) with Structure, Speakers, Section overrides, and Script settings tabs." },
  { page: "Audio Editor (Ctrl+6)", desc: "Non-destructive waveform editor with selection, cut/copy/paste/delete, trim, split, move, duplicate, join, silence, fade, gain, normalize, 8-stage DSP enhance, undo/redo, and loop playback." },
  { page: "Voice Editor (Ctrl+9)", desc: "Edit a voice’s name, model, engine voice, and delivery (speed, pitch, energy, emotion, style). Preview it, then use that saved voice in Generate and script-to-audio." },
  { page: "Voices (Ctrl+7)", desc: "Cloned voices plus every built-in preset: Piper Lessac (the default voice), all 54 Kokoro voices, and the Edge neural catalog. Preview, edit, export metadata, revoke, or delete." },
  { page: "Models (Ctrl+8)", desc: "Download weights directly from Hugging Face (single model or Download All), load/unload into CPU or CUDA memory, run health checks, set defaults, and rescan data/models/." },
  { page: "Settings (Ctrl+,)", desc: "Configure default TTS/cloning models, compute device (auto/cpu/cuda), online engine opt-in, editor autosave, appearance/theme, native title bar, and embedded REST API + MCP server." },
] as const

const SHORTCUTS = [
  { key: "Ctrl+Shift+P / F1", action: "Open the Command Palette to search and trigger any menu command" },
  { key: "Ctrl+1 … Ctrl+9", action: "Switch between Home, Studio, Clone, Generate, Script, Editor, Voices, Models, and Voice Editor (Ctrl+9)" },
  { key: "Ctrl+,", action: "Open Settings" },
  { key: "Ctrl+B", action: "Collapse or expand the navigation sidebar" },
  { key: "Ctrl+`", action: "Toggle the bottom live Logs panel (with source filter & warning/error badges)" },
  { key: "Ctrl+J", action: "Open the Background Jobs monitor dialog" },
  { key: "Ctrl+Shift+N", action: "Create a new workspace project (File → New Project…)" },
  { key: "Ctrl+N", action: "Create a new script on the Script to Audio page" },
  { key: "Ctrl+O / Ctrl+I", action: "Open an existing audio or import an audio file into the Audio Editor" },
  { key: "Space", action: "Play / Pause transport in the Audio Editor" },
  { key: "Ctrl+Z / Ctrl+Shift+Z", action: "Undo / Redo in focused text input or non-destructive Audio Editor" },
  { key: "Ctrl+X / Ctrl+C / Ctrl+V / Del", action: "Cut, Copy, Paste, or Delete selection in text box or Audio Editor" },
  { key: "Ctrl+D / Ctrl+T", action: "Duplicate selection or Trim (crop) to selection in the Audio Editor" },
  { key: "Ctrl+S / Ctrl+E", action: "Render pending edits as a new audio row / Export audio to WAV, FLAC, OGG, MP3, or M4A" },
  { key: "F11 / Ctrl+Q", action: "Toggle Full Screen / Exit VoxLabs" },
] as const

const PACKAGES = [
  { pkg: "app/main.py", contents: "Desktop entry point: initialize services, create QApplication and MainWindow, optionally start the embedded REST API + MCP server." },
  { pkg: "app/services/", contents: "One service per domain: user, voice, clone, consent, tts, script, audio, project, model, job, system. Each exposes a module singleton (tts_service, …)." },
  { pkg: "app/models/", contents: "SQLAlchemy 2.0 tables (one file per table, no commits or workflow logic). models/request/ and models/response/ hold Pydantic request classes and ApiResponse." },
  { pkg: "app/utils/", contents: "Technical infrastructure: database (engine, transaction(), serialize()), audio (I/O and DSP), ffmpeg, files, device, validation (Validation), model (AI backends), hashing, time, logger." },
  { pkg: "app/constants/", contents: "Fixed values and BaseEnum classes: base_enum, status, consent_status, response_status, error_code, error_message, project_type, audio_source, model_type, model_backend, audio, jobs, models." },
  { pkg: "app/exceptions/", contents: "AppError and subclasses (ValidationError, NotFoundError, ConsentError, VoiceError, AudioError, ModelError, JobError, ProjectError, AuthError, InternalError) + service_error()." },
  { pkg: "app/api/", contents: "FastAPI app (app.py), thin routers in routes/, and MCP server in mcp/ (tools.py, served over streamable HTTP at /mcp and over stdio with --stdio)." },
  { pkg: "app/ui/", contents: "main_window.py, 10 pages, shared widgets (title_bar, nav_bar, command_palette, player, waveform, timeline, log_panel, job_status), app_menu.py, theme.py, and icons.py." },
] as const

const TTS_PARAMETERS = [
  { param: "voices_id", range: "int | null", notes: "Cloned or preset voice ID. Omit it to use the engine's default voice." },
  { param: "engine_voice", range: "short id", notes: "One of the engine's built-in voices, e.g. Kokoro af_heart / af_bella / bm_george or an Edge short name. Overrides the voice's own engine_voice." },
  { param: "model_key", range: "string | null", notes: "Resolved in order: explicit key → voice's own cloning model (if installed) → default_tts_model → first installed fallback model." },
  { param: "speed, pitch", range: "0.5 – 2.0", notes: "Passed to the engine when supported natively; otherwise applied with float64 phase-vocoder DSP." },
  { param: "energy", range: "0.1 – 2.0", notes: "Output gain multiplier with automatic peak protection." },
  { param: "emotion", range: "8 presets", notes: "neutral, happy, sad, angry, calm, excited, fearful, confident. Preset multiplier on speed/pitch/energy; Chatterbox handles emotion natively." },
  { param: "style", range: "6 presets", notes: "default, narration, conversational, lecture, news, storytelling. Adjusts speed and inter-sentence pause." },
  { param: "pause_ms", range: "≥ 0 ms", notes: "Gap between chunks. You can also write [pause 800ms] or [pause 2s] inline in the text." },
  { param: "pronunciations", range: "{word: spoken}", notes: "Whole-word case-insensitive replacement applied before synthesis." },
  { param: "temperature", range: "0.1 – 1.5", notes: "Sampling temperature (XTTS v2 and Chatterbox only)." },
  { param: "seed", range: "int", notes: "Deterministic generation seed (F5-TTS and Chatterbox only)." },
  { param: "post / preset", range: "steps | name", notes: "Clean-up DSP steps or preset name. Default is trim_silence + normalize; {} means raw output." },
  { param: "cache", range: "bool", notes: "When true, returns an identical earlier generation matching text + settings + model + voice hash without re-synthesizing." },
] as const

const ENGINE_DETAILS = [
  { backend: "Piper", install: "uv sync --extra piper + install on Models page", runs: "Local CPU / GPU (63 MB)", native: "speed; direct ONNX weight download" },
  { backend: "Kokoro 82M", install: "uv sync --extra kokoro + install on Models page", runs: "Local CPU / GPU (330 MB)", native: "speed; built-in voices via engine_voice (default af_heart)" },
  { backend: "Coqui XTTS v2", install: "uv sync --extra xtts (CPML non-commercial)", runs: "Local GPU rec. / CPU fallback (2.08 GB)", native: "speed, temperature; multilingual zero-shot cloning" },
  { backend: "F5-TTS", install: "uv sync --extra f5 (MIT)", runs: "Local GPU rec. / CPU fallback (1.40 GB)", native: "speed, seed; flow-matching zero-shot cloning" },
  { backend: "Chatterbox", install: "uv sync --extra chatterbox (MIT)", runs: "Local GPU rec. / CPU fallback (3.20 GB)", native: "emotion, temperature, seed; zero-shot cloning or built-in voice" },
  { backend: "Voice Profile (MFCC)", install: "Built into base install (librosa)", runs: "Local CPU", native: "Extracts MFCC + pYIN median pitch; pitch-matches default TTS output" },
  { backend: "Emotional (gTTS)", install: "Built into base install", runs: "Online (Google), opt-in only", native: "Shaped with local prosody DSP afterwards" },
  { backend: "Edge Neural", install: "Built into base install", runs: "Online (Microsoft), opt-in only", native: "speed, pitch; preset voices via engine_voice (default en-US-AriaNeural)" },
] as const

const DSP_STEPS = [
  { step: "1. trim_silence", impl: "Frame RMS threshold with leading/trailing padding", options: "threshold_db, pad_ms" },
  { step: "2. denoise", impl: "STFT spectral gating against the quietest 15% of frames", options: "strength (0 – 1)" },
  { step: "3. eq", impl: "RBJ biquad high-pass, presence peak (3 kHz), low peak, high shelf", options: "highpass_hz, presence_db, low_db, high_db" },
  { step: "4. compress", impl: "RMS envelope follower with static compression curve", options: "threshold_db, ratio, makeup_db" },
  { step: "5. deess", impl: "High-band (6 kHz) dynamic sibilance reduction", options: "frequency, threshold_db, ratio" },
  { step: "6. normalize", impl: "Peak amplitude normalization", options: "peak_db" },
  { step: "7. limit", impl: "5 ms peak-hold gain envelope followed by hard ceiling", options: "ceiling_db" },
  { step: "8. loudness", impl: "K-weighted BS.1770-style gated loudness gain, then limiter", options: "target_lufs, ceiling_db" },
] as const

const DSP_PRESETS = [
  { preset: "Raw", description: "No DSP steps applied; preserves the exact raw waveform." },
  { preset: "Voice Clean", description: "Trims silence, applies gentle spectral denoise, high-pass filter, and peak normalization." },
  { preset: "Podcast", description: "Denoise, presence EQ boost, vocal compression, de-esser, limiter, and −16 LUFS broadcast loudness." },
  { preset: "Narration", description: "Warm EQ, smooth compression, de-esser, and −18 LUFS audiobook/narration loudness." },
  { preset: "Lesson", description: "Clear speech intelligibility EQ, compression, and −16 LUFS loudness for educational content." },
  { preset: "Studio", description: "Full 8-stage vocal mastering chain targeting −14 LUFS." },
] as const

const EDITOR_OPS = [
  { op: "delete / cut", fields: "start, end", desc: "Remove the selected time range (cut also saves the selection to a clip)." },
  { op: "crop / trim", fields: "start, end", desc: "Keep only the selected time range and discard the rest." },
  { op: "insert / paste", fields: "at, clip", desc: "Insert a saved WAV clip from save_clip() at the cursor timestamp." },
  { op: "append", fields: "clip, gap", desc: "Join another audio file onto the end with an optional silence gap." },
  { op: "silence", fields: "at, duration", desc: "Insert pure silence of duration seconds at the cursor." },
  { op: "duplicate", fields: "start, end", desc: "Copy the selected region immediately after itself." },
  { op: "move", fields: "start, end, to", desc: "Cut the selected region and insert it at timestamp to." },
  { op: "gain / volume", fields: "start, end, db", desc: "Apply decibel gain adjustment over the selected region." },
  { op: "fade_in / fade_out", fields: "start, end", desc: "Apply a smooth fade-in or fade-out ramp over the selection." },
  { op: "normalize", fields: "start, end, peak_db", desc: "Peak-normalize the selected region to peak_db." },
  { op: "enhance", fields: "start, end, steps | preset", desc: "Run any DSP preset or custom step dictionary on the selected region." },
] as const

const DB_TABLES = [
  { table: "users", purpose: "Local operator profiles", columns: "users_id, name, email, status, created_at, updated_at" },
  { table: "voices", purpose: "Cloned or preset voices", columns: "voices_id, users_id, name, language, model_key, source (clone/preset), engine_voice, consent_status, profile (JSON), storage_dir, sample_count" },
  { table: "voice_samples", purpose: "Reference recordings", columns: "voice_samples_id, voices_id, path, duration, sample_rate, quality (JSON), sha256" },
  { table: "voice_consents", purpose: "Consent audit trail", columns: "voice_consents_id, voices_id, granted_by, speaker_name, statement, granted_at, revoked_at" },
  { table: "audios", purpose: "Every audio file", columns: "audios_id, projects_id, parent_audios_id, path, original_path, source, ai_generated, duration, sample_rate, channels, format, codec, file_size, loudness, params (JSON), edit_ops (JSON)" },
  { table: "projects", purpose: "Optional workspace grouping", columns: "projects_id, users_id, name, project_type, settings, edit_state (JSON)" },
  { table: "scripts", purpose: "Scripts and lessons", columns: "scripts_id, projects_id, title, body, speaker_map, settings, final_audios_id" },
  { table: "script_sections", purpose: "Generatable script units", columns: "script_sections_id, scripts_id, position, chapter, heading, speaker, text, voice/speed/pitch/emotion/style overrides, pause_after_ms" },
  { table: "takes", purpose: "Renditions of a section", columns: "takes_id, script_sections_id, audios_id, take_number, selected" },
  { table: "jobs", purpose: "Background work records", columns: "jobs_id, users_id, job_type, title, progress, error, params, result, started_at, finished_at" },
  { table: "models", purpose: "Model catalog state", columns: "models_id, key, name, model_type, backend, version, size_mb, vram_mb, capabilities, online, installed_path" },
] as const

const ERROR_CODES = [
  { code: "400", exc: "AppError, AudioError, ProjectError", meaning: "Bad request or invalid domain operation" },
  { code: "401", exc: "AuthError", meaning: "Missing or invalid bearer API token" },
  { code: "403", exc: "ConsentError", meaning: "Missing, invalid, or revoked speaker consent" },
  { code: "404", exc: "NotFoundError", meaning: "Requested record or route was not found" },
  { code: "409", exc: "VoiceError, JobError", meaning: "Conflict with current voice or job state" },
  { code: "422", exc: "ValidationError", meaning: "Invalid request field(s); field maps each field name to its message" },
  { code: "500", exc: "InternalError", meaning: "Unexpected exception (logged once via service_error(); stack traces are never returned)" },
  { code: "503", exc: "ModelError", meaning: "Model not installed, online engines disabled, or model load failure" },
] as const

const API_ENDPOINTS = [
  { route: "GET /api/health, GET /api/presets", request: "—", service: "system_service.health() / presets()" },
  { route: "GET /api/users, GET /api/users/{id}", request: "—", service: "user_service.list_users() / get_user()" },
  { route: "POST /api/users", request: "UserRequest", service: "user_service.save(body) (create / update / delete)" },
  { route: "GET /api/voices, GET /api/voices/{id}", request: "—", service: "voice_service.list_voices() / get()" },
  { route: "POST /api/voices", request: "VoiceRequest", service: "voice_service.save(body) (creates/updates/deletes preset voices)" },
  { route: "POST /api/voices/clone", request: "CloneRequest (multipart)", service: "clone_service.clone_upload(body)" },
  { route: "POST /api/voices/analyze", request: "multipart sample", service: "clone_service.analyze_upload()" },
  { route: "POST /api/voices/{id}/revoke, GET .../export", request: "—", service: "voice_service.revoke() / export_metadata()" },
  { route: "POST /api/voices/{id}/samples, POST .../samples/{sid}/remove", request: "multipart audio", service: "voice_service.attach_upload() / remove_sample()" },
  { route: "POST /api/tts", request: "TTSRequest", service: "tts_service.generate(body) / generate_async(body)" },
  { route: "POST /api/tts/regenerate", request: "RegenerateRequest", service: "tts_service.regenerate(body)" },
  { route: "GET /api/scripts, GET /api/scripts/{id}", request: "—", service: "script_service.list_scripts() / get()" },
  { route: "POST /api/scripts", request: "ScriptRequest", service: "script_service.save(body)" },
  { route: "POST /api/scripts/{id}/generate", request: "GenerateScriptRequest", service: "script_service.generate(id, body) / generate_async(id, body)" },
  { route: "POST /api/scripts/sections", request: "SectionRequest", service: "script_service.update_section(body)" },
  { route: "POST /api/scripts/sections/{id}/generate, POST .../takes/{id}/select", request: "—", service: "script_service.generate_section() / select_take()" },
  { route: "GET /api/audio, GET /api/audio/{id}, GET /api/audio/{id}/file", request: "—", service: "audio_service.list_audios() / get() / file download" },
  { route: "POST /api/audio/import", request: "AudioImportRequest (multipart)", service: "audio_service.import_upload(body)" },
  { route: "POST /api/audio/process", request: "AudioProcessRequest", service: "audio_service.process(body) (steps/preset or editor ops list)" },
  { route: "POST /api/audio/export", request: "AudioExportRequest", service: "audio_service.export(body), returns the exported file" },
  { route: "GET /api/projects, GET /api/projects/{id}", request: "—", service: "project_service.list_projects() / open_project()" },
  { route: "POST /api/projects, POST /api/projects/{id}/duplicate", request: "ProjectRequest", service: "project_service.save(body) / duplicate_project()" },
  { route: "GET /api/models, GET /api/models/{id}, GET .../health", request: "—", service: "model_service.list_models() / get() / health()" },
  { route: "POST /api/models/install-all", request: "accept_license", service: "model_service.install_all_async(accept_license)" },
  { route: "POST /api/models/{id}/install | load | unload", request: "accept_license", service: "model_service.install_async() / load_async() / unload()" },
  { route: "GET /api/jobs, GET /api/jobs/{id}, POST /api/jobs/{id}/cancel", request: "—", service: "job_service.list_jobs() / get_job() / cancel()" },
] as const

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground pt-10 pb-24 px-6">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-[250px_1fr] gap-12">
        {/* Sticky Table of Contents */}
        <aside className="hidden lg:block">
          <div className="sticky top-24 space-y-4 border-r border-border/40 pr-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              VoxLabs 3.0 Manual
            </p>
            <nav className="flex flex-col space-y-1.5 text-sm text-muted-foreground">
              {DOC_SECTIONS.map((s) => (
                <a
                  key={s.id}
                  href={`#${s.id}`}
                  className="hover:text-foreground transition-colors py-1"
                >
                  {s.label}
                </a>
              ))}
            </nav>
            <div className="pt-4 border-t border-border/40 space-y-2 text-xs text-muted-foreground">
              <p>LLM / Agent Context:</p>
              <div className="flex gap-3">
                <Link href="/llms.txt" className="underline underline-offset-4 hover:text-foreground">
                  llms.txt
                </Link>
                <Link href="/llms-full.txt" className="underline underline-offset-4 hover:text-foreground">
                  llms-full.txt
                </Link>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <div className="max-w-4xl space-y-20">
          {/* Header */}
          <div className="space-y-6 border-b border-border/40 pb-12">
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
              Documentation
            </h1>
            <p className="text-xl text-muted-foreground leading-relaxed">
              VoxLabs is a local-first Python desktop application (PySide6) with an optional FastAPI REST API and Model Context Protocol (MCP) server. This manual covers every feature, page, model engine, DSP stage, database table, and API endpoint in VoxLabs 3.0.
            </p>
            <div className="flex flex-wrap gap-3">
              <a href={RELEASES_URL}>
                <Button>
                  Download Desktop App
                  <Download className="ml-2 w-4 h-4" />
                </Button>
              </a>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
                <Button variant="outline">View Source on GitHub</Button>
              </a>
            </div>
          </div>

          {/* 1. Installation & Setup */}
          <section id="install" className="space-y-6 scroll-mt-24">
            <h2 className="text-3xl font-bold flex items-center gap-3">
              <Monitor className="w-7 h-7 text-indigo-400" />
              1. Installation &amp; Quick Start
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              You can install VoxLabs using the prebuilt standalone desktop archives (no Python installation needed) or run it from source using Python 3.12–3.13 and <a href="https://docs.astral.sh/uv/" target="_blank" rel="noopener noreferrer" className="text-foreground underline underline-offset-4">uv</a>.
            </p>

            <div className="space-y-3">
              <h3 className="text-xl font-semibold">Option A: Standalone Desktop Bundles</h3>
              <ol className="list-decimal list-inside space-y-2 text-muted-foreground leading-relaxed">
                <li>Open the <Link href="/#download" className="text-foreground underline underline-offset-4">download section</Link> or <a href={RELEASES_URL} className="text-foreground underline underline-offset-4">GitHub Releases</a> and download the archive for your OS.</li>
                <li><strong>Windows (10 or later, x64):</strong> Run <code>VoxLabs-Windows-x64-Setup.exe</code> (no admin needed) or install <code>VoxLabs-Windows-x64.msi</code>. For a portable copy, extract <code>VoxLabs-Windows-x64.zip</code> and launch <code>VoxLabs\VoxLabs.exe</code>.</li>
                <li><strong>macOS (13 Ventura or later, Apple Silicon):</strong> Open <code>VoxLabs-macOS-arm64.dmg</code> and drag <code>VoxLabs.app</code> to your Applications folder, or run <code>VoxLabs-macOS-arm64.pkg</code>.</li>
                <li><strong>Linux (x86_64):</strong> Ubuntu/Debian: <code>sudo apt install ./VoxLabs-Linux-x86_64.deb</code>. Fedora: <code>sudo dnf install ./VoxLabs-Linux-x86_64.rpm</code>. Then start VoxLabs from the app menu or run <code>voxlabs</code>. For a portable copy, extract <code>VoxLabs-Linux-x86_64.tar.gz</code> and run <code>VoxLabs/VoxLabs</code>.</li>
                <li>Because community builds are not code-signed with a commercial certificate yet, confirm the first launch if Windows SmartScreen or macOS Gatekeeper prompts you.</li>
              </ol>
              <p className="text-xs text-muted-foreground">
                <strong>Audio formats:</strong> WAV, FLAC, OGG, and MP3 work out of the box via <code>libsndfile</code>. Having <code>ffmpeg</code> on your system <code>PATH</code> is optional and enables M4A/AAC import and export.
              </p>
            </div>

            <div className="space-y-3">
              <h3 className="text-xl font-semibold">Option B: Run from Source with uv</h3>
              <pre className="rounded-xl border border-border/50 bg-secondary/40 p-4 text-xs sm:text-sm font-mono overflow-x-auto leading-relaxed">
{`git clone https://github.com/nishanth-kj/VoxLabs.git
cd VoxLabs

# Base install (includes PySide6 UI, FastAPI, MCP, DSP enhancement, and MFCC voice profiles)
uv sync

# Recommended fast offline neural TTS engines (run well on CPU or GPU)
uv sync --extra piper --extra kokoro

# Optional heavy zero-shot cloning engines (mutually exclusive PyTorch dependencies; pick one):
uv sync --extra xtts             # Coqui XTTS v2 (non-commercial CPML license)
uv sync --extra f5               # F5-TTS (MIT)
uv sync --extra chatterbox       # Chatterbox TTS (MIT, zero-shot cloning + native emotion)

# Start the desktop application
uv run python -m app.main`}
              </pre>
              <p className="text-sm text-muted-foreground leading-relaxed">
                <strong>First launch:</strong> Open the <strong>Models</strong> page and click <strong>Download All</strong> (or install <em>Piper · en_US Lessac</em>, 63 MB). Model weights are fetched directly from Hugging Face and stored under <code>data/models/</code>, even if a model&apos;s Python extra has not been installed yet. On slow connections, increase uv&apos;s timeout before syncing PyTorch wheels (e.g. in PowerShell: <code>$env:UV_HTTP_TIMEOUT = &quot;900&quot;; uv sync --extra piper</code>).
              </p>
            </div>

            <div className="space-y-3">
              <h3 className="text-xl font-semibold">Environment Variables</h3>
              <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Variable</TableHead>
                      <TableHead>Effect</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {ENV_VARS.map((v) => (
                      <TableRow key={v.name}>
                        <TableCell className="font-mono text-xs font-semibold">{v.name}</TableCell>
                        <TableCell className="text-sm text-muted-foreground whitespace-normal">{v.effect}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          </section>

          {/* 2. Desktop Studio & Shortcuts */}
          <section id="desktop-ui" className="space-y-6 scroll-mt-24 border-t border-border/40 pt-16">
            <h2 className="text-3xl font-bold flex items-center gap-3">
              <LayoutGrid className="w-7 h-7 text-purple-400" />
              2. Desktop Studio Pages &amp; Keyboard Shortcuts
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              The VoxLabs window follows a modern VS Code–inspired layout:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground leading-relaxed">
              <li><strong>Title Bar &amp; Command Center:</strong> Displays the VoxLabs logo, the full application menu bar (<strong>File, Edit, View, Voice, Audio, Script, Tools, Help</strong>), a central search button that opens the Command Palette, and native-snapping window controls. Enable <strong>Settings → Appearance → Use the system title bar</strong> if you prefer your OS&apos;s native window frame.</li>
              <li><strong>Every Command in the Menu &amp; Palette:</strong> Every action on every page is reachable from the top menu bar and searchable in the Command Palette (<code>Ctrl+Shift+P</code> or <code>F1</code>). Selecting a page command automatically navigates to that page and invokes its action.</li>
              <li><strong>Workspace Project Scoping:</strong> Use <strong>File → New Project… / Open Project… / Close Project</strong> (or click the project button in the bottom status bar) to scope work to a project. While a project is open, new speech generations, scripts, and audio imports belong to that project, and lists filter to it; when closed, all work is shown. The active project is remembered across restarts.</li>
              <li><strong>Status Bar &amp; Live Logs Panel:</strong> The bottom status bar shows the open project, the REST API / MCP server state (click to start or stop), active background jobs, and the <strong>Logs</strong> toggle (<code>Ctrl+`</code>) with live warning/error counts and source filters (<code>ui</code>, <code>api</code>, <code>mcp</code>, <code>system</code>).</li>
            </ul>

            <h3 className="text-xl font-semibold pt-2">Pages Reference</h3>
            <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Page</TableHead>
                    <TableHead>What It Does</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {DESKTOP_PAGES.map((p) => (
                    <TableRow key={p.page}>
                      <TableCell className="font-semibold text-xs whitespace-nowrap">{p.page}</TableCell>
                      <TableCell className="text-sm text-muted-foreground whitespace-normal">{p.desc}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <h3 className="text-xl font-semibold pt-2">Keyboard Shortcuts</h3>
            <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Shortcut</TableHead>
                    <TableHead>Command</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {SHORTCUTS.map((s) => (
                    <TableRow key={s.key}>
                      <TableCell className="font-mono text-xs font-semibold whitespace-nowrap">{s.key}</TableCell>
                      <TableCell className="text-sm text-muted-foreground whitespace-normal">{s.action}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>

          {/* 3. Architecture & Flow */}
          <section id="architecture" className="space-y-6 scroll-mt-24 border-t border-border/40 pt-16">
            <h2 className="text-3xl font-bold flex items-center gap-3">
              <Layers className="w-7 h-7 text-indigo-400" />
              3. Architecture, Packages &amp; Background Work
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              VoxLabs is organized into a single Python package, <code>app/</code>, with strict separation of concerns. The PySide6 UI, the FastAPI REST routes, and the MCP tools all call the same service singletons—never touching SQLite or AI model backends directly.
            </p>
            <pre className="rounded-xl border border-border/50 bg-secondary/40 p-4 text-xs sm:text-sm font-mono overflow-x-auto leading-relaxed">
{`PySide6 UI (app/ui)     REST API + MCP (app/api)   ← optional interfaces
          \\                     /
           Services (app/services)                 ← all application logic & transactions
           /                    \\
   Models (app/models)       Utils (app/utils)
           \\                    /
          SQLite + files under data/`}
            </pre>

            <h3 className="text-xl font-semibold pt-2">Package Map</h3>
            <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Package</TableHead>
                    <TableHead>Responsibilities</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {PACKAGES.map((p) => (
                    <TableRow key={p.pkg}>
                      <TableCell className="font-mono text-xs font-semibold whitespace-nowrap">{p.pkg}</TableCell>
                      <TableCell className="text-sm text-muted-foreground whitespace-normal">{p.contents}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="space-y-3 text-sm text-muted-foreground leading-relaxed">
              <h3 className="text-xl font-semibold text-foreground">How a Request Flows</h3>
              <ol className="list-decimal list-inside space-y-1.5">
                <li>Clicking <strong>Generate</strong> on the Generate page builds a <code>TTSRequest</code> and calls <code>tts_service.generate_async(body)</code> (or <code>POST /api/tts</code> / MCP <code>generate_speech</code> calls <code>tts_service.generate(body)</code>).</li>
                <li><code>JobService.submit()</code> records a <code>jobs</code> row (<code>status = Pending</code>) and dispatches the work on a background thread pool.</li>
                <li><code>TTSService.generate()</code> validates input, resolves the voice via <code>VoiceService.voice_ref()</code> (checking consent), resolves the model via <code>ModelService.resolve_speech_model()</code>, loads the backend, synthesizes chunk-by-chunk, applies prosody and DSP clean-up, and registers an <code>audios</code> row inside a single transaction.</li>
                <li>Job progress and completion are written to SQLite and pushed to listeners. <code>JobBridge</code> turns updates into Qt signals so <code>BasePage.follow()</code> updates the progress bar on the UI thread without ever blocking Qt.</li>
              </ol>
              <p>
                <strong>Errors &amp; Logging:</strong> Every public service method wraps its body in <code>try: ... except Exception as exc: raise service_error(exc, &quot;&lt;service&gt;.&lt;method&gt;&quot;)</code>. Known <code>AppError</code> subclasses pass through; unexpected exceptions are logged once with their traceback and converted into <code>InternalError</code>. <code>app/utils/logger.py</code> writes to <code>stderr</code> (keeping <code>stdout</code> clean for MCP stdio), the memory buffer for the bottom Logs panel, and rotating files in <code>data/logs/voxlabs.log</code>. Audio content, file bytes, and credentials are never logged.
              </p>
            </div>
          </section>

          {/* 4. Voice Cloning & Consent */}
          <section id="voice-cloning" className="space-y-6 scroll-mt-24 border-t border-border/40 pt-16">
            <h2 className="text-3xl font-bold flex items-center gap-3">
              <Mic className="w-7 h-7 text-pink-400" />
              4. Voice Cloning &amp; Consent Lifecycle
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Voice cloning is managed by <code>CloneService</code>, <code>ConsentService</code>, and <code>VoiceService</code>. Explicit, attributed consent is verified before any sample is processed.
            </p>
            <pre className="rounded-xl border border-border/50 bg-secondary/40 p-4 text-xs sm:text-sm font-mono overflow-x-auto leading-relaxed">
{`samples → validate files → validate consent → select model
        → analyze + prepare samples (staging folder) → build profile
        → [one transaction: create voice → record consent → move samples in → store profile]
        → voice ready for TTS → preview`}
            </pre>

            <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground leading-relaxed">
              <li><strong>Validate files (<code>require_audio_file</code>):</strong> Verifies each file exists, is non-empty, and has a supported extension (<code>wav</code>, <code>mp3</code>, <code>flac</code>, <code>ogg</code>, <code>m4a</code>, <code>aac</code>, <code>opus</code>).</li>
              <li><strong>Validate consent (<code>ConsentService.validate</code>):</strong> Requires <code>confirmed is True</code>, plus non-empty <code>granted_by</code> and <code>speaker_name</code>. Runs before any audio work; nothing can bypass it.</li>
              <li><strong>Select model:</strong> Uses the requested <code>model_key</code> or <code>default_clone_model</code> from Settings (must be an installed <code>CLONE</code> or <code>EMBED</code> model).</li>
              <li><strong>Analyze (<code>analyze_sample</code>):</strong> Runs <code>AudioService.analyze</code> and blocks on samples shorter than 1 s or longer than 5 min, sample rates under 16 kHz, or more than 90% silence. Clipping, high noise floor, and low level are reported as warnings.</li>
              <li><strong>Prepare samples:</strong> Resamples each file to 24 kHz mono, trims leading/trailing silence, peak-normalizes to −1 dBFS, and writes to a staging folder. Combined samples must provide at least 3 seconds of speech.</li>
              <li><strong>Build profile (<code>build_profile</code>):</strong> Computes 13-band MFCC mean/std vectors and median fundamental frequency (pYIN) across all prepared samples.</li>
              <li><strong>Atomic transaction:</strong> Creates the <code>voices</code> row, records the <code>voice_consents</code> row, moves prepared samples into <code>data/voices/&lt;voices_id&gt;/samples/</code>, and stores the profile. On any error, the database transaction rolls back and both staging and voice folders are removed.</li>
            </ol>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="rounded-xl border border-border/40 bg-card/50 p-5 space-y-2">
                <h3 className="font-semibold text-base">Zero-Shot vs. Profile vs. Preset</h3>
                <p className="text-muted-foreground leading-relaxed">
                  <strong>XTTS v2, F5-TTS, Chatterbox:</strong> Receive stored reference WAV paths for true zero-shot voice cloning (<code>params.cloned = true</code>).<br />
                  <strong>Voice Profile (MFCC):</strong> Speaks through the default TTS model and shifts output pitch to match the speaker&apos;s median pitch (<code>params.pitch_matched = true</code>).<br />
                  <strong>Preset Voices:</strong> Built-in engine speakers (e.g. Kokoro or Edge <code>engine_voice</code>); nobody is cloned, so <code>consent_status = NotRequired</code>.
                </p>
              </div>
              <div className="rounded-xl border border-border/40 bg-card/50 p-5 space-y-2">
                <h3 className="font-semibold text-base">Revoking vs. Deleting a Voice</h3>
                <p className="text-muted-foreground leading-relaxed">
                  <strong>Revoke (<code>voice_service.revoke</code>):</strong> (1) Deletes all sample files and the profile from disk, (2) marks consent rows <code>Inactive</code> with <code>revoked_at</code>, (3) sets <code>voices.status = Inactive</code> and <code>consent_status = Revoked</code>, and (4) blocks the voice from synthesis while keeping the row as an audit trail.<br />
                  <strong>Delete (<code>voice_service.delete</code>):</strong> Removes the voice row, sample rows, consent rows, and disk folder completely.
                </p>
              </div>
            </div>
          </section>

          {/* 5. Text to Speech & Models */}
          <section id="tts" className="space-y-6 scroll-mt-24 border-t border-border/40 pt-16">
            <h2 className="text-3xl font-bold flex items-center gap-3">
              <Cpu className="w-7 h-7 text-cyan-400" />
              5. Text to Speech (TTS) &amp; Model Engines
            </h2>
            <pre className="rounded-xl border border-border/50 bg-secondary/40 p-4 text-xs sm:text-sm font-mono overflow-x-auto leading-relaxed">
{`text → validate → pronunciations → resolve voice → resolve model → load backend
     → chunk (sentence-aligned, [pause] tags; ≤ 400 chars, or the engine's own limit)
     → synthesize each chunk (one generation at a time per engine)
     → join with pauses → pitch-match (profile voices) → prosody DSP
     → save original WAV → clean-up steps → processed WAV → audios row (ai_generated)`}
            </pre>
            <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground leading-relaxed">
              <li><strong>Deterministic Cache (<code>cache: true</code>):</strong> Hashes text, speech parameters, resolved model, and voice update timestamp; returns the newest matching generated audio whose file still exists on disk with <code>cached: true</code>.</li>
              <li><strong>GPU OOM → CPU Fallback:</strong> When a model runs out of CUDA memory while loading (e.g. when a local LLM is running), VoxLabs frees CUDA cache and reloads the model on CPU automatically.</li>
              <li><strong>Fallback Models:</strong> When no model is explicitly requested and <code>default_tts_model</code> is not installed, VoxLabs uses the first installed model in <code>FALLBACK_TTS_MODELS</code> (<code>chatterbox</code> → <code>kokoro-82m</code> → <code>piper-en-us-lessac-medium</code>).</li>
              <li><strong>Sentence-Level Regeneration:</strong> <code>generate_sentences(text)</code> creates one audio per sentence plus a joined result; <code>regenerate_sentence(audios_ids, index)</code> re-synthesizes a single sentence and rebuilds the joined audio.</li>
            </ul>

            <h3 className="text-xl font-semibold pt-2">TTS Parameters</h3>
            <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Parameter</TableHead>
                    <TableHead>Range / Type</TableHead>
                    <TableHead>Notes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {TTS_PARAMETERS.map((row) => (
                    <TableRow key={row.param}>
                      <TableCell className="font-mono text-xs font-semibold whitespace-nowrap">{row.param}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground whitespace-nowrap">{row.range}</TableCell>
                      <TableCell className="text-sm text-muted-foreground whitespace-normal">{row.notes}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <h3 className="text-xl font-semibold pt-2">Engines Reference</h3>
            <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Backend</TableHead>
                    <TableHead>Install</TableHead>
                    <TableHead>Execution</TableHead>
                    <TableHead>Native Capabilities</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ENGINE_DETAILS.map((e) => (
                    <TableRow key={e.backend}>
                      <TableCell className="font-semibold text-xs whitespace-nowrap">{e.backend}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground whitespace-normal">{e.install}</TableCell>
                      <TableCell className="text-xs text-muted-foreground whitespace-normal">{e.runs}</TableCell>
                      <TableCell className="text-sm text-muted-foreground whitespace-normal">{e.native}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>

          {/* 6. Script & Lesson to Audio */}
          <section id="script-to-audio" className="space-y-6 scroll-mt-24 border-t border-border/40 pt-16">
            <h2 className="text-3xl font-bold flex items-center gap-3">
              <FileText className="w-7 h-7 text-amber-400" />
              6. Script &amp; Lesson to Audio
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              <code>ScriptService</code> turns scripts, lessons, and multi-speaker dialogues into narrated audio with automatic chapter/section structure and per-section take management.
            </p>
            <pre className="rounded-xl border border-border/50 bg-secondary/40 p-4 text-xs sm:text-sm font-mono overflow-x-auto leading-relaxed">
{`Lesson 1                       ← chapter  (Lesson/Chapter/Part/Unit/Module …, or "# Title")

Introduction                   ← heading  (Section/Topic/Scene/Introduction/Summary/Example …,
                                            "## Title", or a short Title Case line)
Welcome to today's lesson.     ← paragraph → one section

Teacher: What is a wave?       ← speaker line → one section (speaker "Teacher")
Student: I'm not sure.
It sounds hard.                ← continues the Student line

[pause 2s]                     ← a line on its own adds pause after the previous section`}
            </pre>
            <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground leading-relaxed">
              <li><strong>Automatic Pauses:</strong> <code>parse_script(body, speak_headings=False)</code> inserts 600 ms between paragraphs, 1200 ms at chapter/heading boundaries, plus any manual <code>[pause …]</code> lines. With <code>speak_headings=True</code>, headings are spoken aloud as sections.</li>
              <li><strong>5-Step Voice Resolution Order:</strong> (1) Section&apos;s own <code>voices_id</code> → (2) <code>speaker_map[speaker]</code> → (3) <code>speaker_map[&quot;*&quot;]</code> (narrator) → (4) <code>default_voices_id</code> setting → (5) Engine&apos;s default voice. Use <code>auto_map_speakers()</code> to assign available voices round-robin.</li>
              <li><strong>Script Settings:</strong> Stored in <code>scripts.settings</code>: <code>model_key</code>, <code>speed</code>, <code>emotion</code>, <code>style</code>, final mastering <code>preset</code>, <code>speak_headings</code>, <code>intro_text</code>, and <code>outro_text</code>.</li>
              <li><strong>Smart Takes &amp; Rendering:</strong> Editing the script body re-parses it while keeping existing takes for any section whose <code>(speaker, text)</code> did not change. <code>render(scripts_id)</code> joins all selected takes with each section&apos;s pause, adds optional intro/outro, applies the final clean-up preset (e.g. <em>Lesson</em> at −16 LUFS), and stores the result as <code>scripts.final_audios_id</code>.</li>
            </ul>
          </section>

          {/* 7. Audio Engine, DSP & Editor */}
          <section id="audio-engine" className="space-y-6 scroll-mt-24 border-t border-border/40 pt-16">
            <h2 className="text-3xl font-bold flex items-center gap-3">
              <Sliders className="w-7 h-7 text-emerald-400" />
              7. Audio Engine, DSP Pipeline &amp; Waveform Editor
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              <code>AudioService</code> and <code>app/utils/audio.py</code> process audio as mono float32 and store working copies as 16-bit WAV. No operation ever overwrites an existing file:
            </p>
            <ul className="list-disc list-inside space-y-1.5 text-sm text-muted-foreground leading-relaxed">
              <li><strong>Import:</strong> Copies the source file to <code>audios.original_path</code> and writes a WAV working copy to <code>audios.path</code>.</li>
              <li><strong>Processing &amp; Rendered Edits:</strong> Create a new <code>audios</code> row with <code>parent_audios_id</code> pointing to the source audio.</li>
              <li><strong>Editor Autosave:</strong> Stores the pending non-destructive operation list directly on the audio row (<code>audios.edit_ops</code> via <code>audio_service.save_edit_ops</code>), so edits persist for every audio file with or without a project.</li>
              <li><strong>Export &amp; AI Labelling:</strong> <code>export(audios_id, dest, fmt, sample_rate)</code> writes WAV, FLAC, OGG, or MP3 via <code>libsndfile</code> and M4A via FFmpeg. AI-generated audio is tagged with <code>comment=&quot;AI-generated by VoxLabs&quot;</code> and <code>software=&quot;VoxLabs&quot;</code>.</li>
            </ul>

            <h3 className="text-xl font-semibold pt-2">8-Stage Enhancement Pipeline</h3>
            <p className="text-sm text-muted-foreground">
              Steps always execute in this fixed order: <code>trim_silence → denoise → eq → compress → deess → normalize → limit → loudness</code>. Passing <code>{`{"step": null}`}</code> disables a step from a preset.
            </p>
            <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Step</TableHead>
                    <TableHead>Implementation</TableHead>
                    <TableHead>Options</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {DSP_STEPS.map((s) => (
                    <TableRow key={s.step}>
                      <TableCell className="font-mono text-xs font-semibold whitespace-nowrap">{s.step}</TableCell>
                      <TableCell className="text-sm text-muted-foreground whitespace-normal">{s.impl}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground whitespace-normal">{s.options}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <h3 className="text-xl font-semibold pt-2">Built-In Enhancement Presets</h3>
            <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Preset</TableHead>
                    <TableHead>Processing Chain</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {DSP_PRESETS.map((p) => (
                    <TableRow key={p.preset}>
                      <TableCell className="font-semibold text-xs whitespace-nowrap">{p.preset}</TableCell>
                      <TableCell className="text-sm text-muted-foreground whitespace-normal">{p.description}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <h3 className="text-xl font-semibold pt-2">Non-Destructive Editor Operations (<code>apply_edit_ops</code>)</h3>
            <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>op</TableHead>
                    <TableHead>Fields (seconds)</TableHead>
                    <TableHead>Description</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {EDITOR_OPS.map((o) => (
                    <TableRow key={o.op}>
                      <TableCell className="font-mono text-xs font-semibold whitespace-nowrap">{o.op}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground whitespace-nowrap">{o.fields}</TableCell>
                      <TableCell className="text-sm text-muted-foreground whitespace-normal">{o.desc}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>

          {/* 8. Database & Transactions */}
          <section id="database" className="space-y-6 scroll-mt-24 border-t border-border/40 pt-16">
            <h2 className="text-3xl font-bold flex items-center gap-3">
              <Database className="w-7 h-7 text-indigo-400" />
              8. Database Schema, Status Enum &amp; Transactions
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              VoxLabs uses SQLite through SQLAlchemy 2.0 (<code>data/database/voxlabs.db</code>) with WAL journaling and foreign keys enabled. Every table uses a plural name, an explicit <code>&lt;table&gt;_id</code> integer primary key, an integer <code>status</code> column backed by <code>BaseEnum</code> (<code>Status.ACTIVE.code == 1</code>, <code>INACTIVE == 2</code>, <code>PENDING == 3</code>, <code>IN_PROGRESS == 4</code>, <code>COMPLETED == 5</code>, <code>FAILED == 6</code>, <code>CANCELLED == 7</code>, <code>DELETED == 8</code>), plus timezone-aware UTC <code>created_at</code> and <code>updated_at</code> timestamps.
            </p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              <strong>In-place upgrades:</strong> <code>init_db()</code> runs <code>create_all()</code> followed by idempotent steps in <code>_upgrade(engine)</code> (such as adding <code>audios.edit_ops</code> and migrating legacy project editor state onto each audio row).
            </p>
            <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Table</TableHead>
                    <TableHead>Purpose</TableHead>
                    <TableHead>Columns</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {DB_TABLES.map((t) => (
                    <TableRow key={t.table}>
                      <TableCell className="font-mono text-xs font-semibold whitespace-nowrap">{t.table}</TableCell>
                      <TableCell className="text-xs text-muted-foreground whitespace-normal">{t.purpose}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground whitespace-normal">{t.columns}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </section>

          {/* 9. REST API & MCP Server */}
          <section id="rest-api-mcp" className="space-y-6 scroll-mt-24 border-t border-border/40 pt-16">
            <h2 className="text-3xl font-bold flex items-center gap-3">
              <Terminal className="w-7 h-7 text-cyan-400" />
              9. REST API &amp; Model Context Protocol (MCP) Server
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              The REST API and MCP server expose the exact same services as the desktop app. Start them from <strong>Settings → REST API</strong> (or <strong>Tools → Run REST API and MCP Server</strong>) inside the desktop app, or run them from the command line:
            </p>
            <pre className="rounded-xl border border-border/50 bg-secondary/40 p-4 text-xs sm:text-sm font-mono overflow-x-auto leading-relaxed">
{`uv run python -m app.api.app                   # REST + MCP over HTTP on 127.0.0.1:8942 (Swagger at /docs, MCP at /mcp)
uv run python -m app.api.app --stdio           # Same HTTP server + MCP over stdin/stdout for local MCP clients
uv run uvicorn app.api.app:app --reload        # Development server on 127.0.0.1:8000`}
            </pre>

            <div className="space-y-3">
              <h3 className="text-xl font-semibold">Response Envelope, Single Save Endpoint &amp; Error Codes</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Every API response—including errors—returns <strong>HTTP 200</strong> with the uniform <code>ApiResponse</code> JSON envelope (<code>status: 1</code> for success, <code>0</code> for error). Each CRUD resource has a single <code>POST /api/&lt;resource&gt;</code> save endpoint: omit <code>&lt;table&gt;_id</code> to create, pass <code>&lt;table&gt;_id</code> to update, or pass <code>&lt;table&gt;_id</code> + <code>&quot;status&quot;: 8</code> (<code>Status.DELETED.code</code>) to delete.
              </p>
              <pre className="rounded-xl border border-border/50 bg-secondary/40 p-4 text-xs sm:text-sm font-mono overflow-x-auto leading-relaxed">
{`{ "status": 1, "data": { ... }, "error": null }

{ "status": 0, "data": null, "error": {
    "error_code": 404,
    "error_message": "The requested item was not found.",
    "field": { "voices_id": "Voice 42 not found" }
} }`}
              </pre>
              <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>error_code</TableHead>
                      <TableHead>Exception Class</TableHead>
                      <TableHead>Meaning</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {ERROR_CODES.map((e) => (
                      <TableRow key={e.code}>
                        <TableCell className="font-mono text-xs font-semibold">{e.code}</TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground whitespace-normal">{e.exc}</TableCell>
                        <TableCell className="text-sm text-muted-foreground whitespace-normal">{e.meaning}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>

            <h3 className="text-xl font-semibold pt-2">All REST Endpoints</h3>
            <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Method &amp; Path</TableHead>
                    <TableHead>Request Class</TableHead>
                    <TableHead>Service Call</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {API_ENDPOINTS.map((e) => (
                    <TableRow key={e.route}>
                      <TableCell className="font-mono text-xs font-semibold whitespace-normal">{e.route}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground whitespace-normal">{e.request}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground whitespace-normal">{e.service}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <h3 className="text-xl font-semibold pt-2">MCP Server Tools &amp; Client Configuration</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              MCP tools in <code>app/api/mcp/tools.py</code> take the same Pydantic request classes and return the same <code>{`{status, data, error}`}</code> envelope. Voice cloning is intentionally omitted from MCP so consent always comes directly from a human speaker.
            </p>
            <div className="rounded-xl border border-border/50 bg-card/50 p-2 sm:p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Domain</TableHead>
                    <TableHead>MCP Tool Names</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-semibold text-xs">System &amp; Users</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground whitespace-normal">health, presets, list_users, save_user</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-semibold text-xs">Voices &amp; Speech</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground whitespace-normal">list_voices, get_voice, save_voice, generate_speech, regenerate_speech</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-semibold text-xs">Audio &amp; Editor</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground whitespace-normal">list_audio, get_audio, process_audio, export_audio</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-semibold text-xs">Scripts &amp; Projects</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground whitespace-normal">list_scripts, get_script, save_script, update_section, generate_script, list_projects, get_project, save_project</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-semibold text-xs">Models &amp; Jobs</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground whitespace-normal">list_models, list_jobs, get_job, cancel_job</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>

            <pre className="rounded-xl border border-border/50 bg-secondary/40 p-4 text-xs sm:text-sm font-mono overflow-x-auto leading-relaxed">
{`// MCP Client Config (Claude Desktop / Cursor / Windsurf / VS Code)
{
  "mcpServers": {
    "voxlabs": {
      "command": "uv",
      "args": ["run", "--directory", "C:/Projects/VoxLabs", "python", "-m", "app.api.app", "--stdio"]
    }
  }
}

# cURL Examples:
# 1. Create, update, and delete a user with the single save endpoint
curl -s -X POST 127.0.0.1:8942/api/users -H 'Content-Type: application/json' -d '{"name": "Ada"}'
curl -s -X POST 127.0.0.1:8942/api/users -H 'Content-Type: application/json' -d '{"users_id": 1, "email": "ada@example.com"}'
curl -s -X POST 127.0.0.1:8942/api/users -H 'Content-Type: application/json' -d '{"users_id": 1, "status": 8}'

# 2. Generate speech with emotion and built-in Kokoro voice
curl -s -X POST 127.0.0.1:8942/api/tts -H 'Content-Type: application/json' \\
  -d '{"text": "Hello from VoxLabs.", "emotion": "calm", "engine_voice": "af_heart"}'

# 3. Clone a voice (consent fields are mandatory)
curl -s -X POST 127.0.0.1:8942/api/voices/clone \\
  -F name="Narrator" -F consent=true -F granted_by="Jane Doe" -F speaker_name="Jane Doe" \\
  -F samples=@jane.wav

# 4. Render a script in the background and poll the job
curl -s -X POST 127.0.0.1:8942/api/scripts/1/generate -H 'Content-Type: application/json' -d '{}'
curl -s 127.0.0.1:8942/api/jobs/12`}
            </pre>
          </section>

          {/* 10. Development, Testing & Extending */}
          <section id="development" className="space-y-6 scroll-mt-24 border-t border-border/40 pt-16">
            <h2 className="text-3xl font-bold flex items-center gap-3">
              <Code2 className="w-7 h-7 text-purple-400" />
              10. Development, Testing &amp; Adding Engines
            </h2>
            <pre className="rounded-xl border border-border/50 bg-secondary/40 p-4 text-xs sm:text-sm font-mono overflow-x-auto leading-relaxed">
{`uv run pytest                                     # Full suite (offscreen Qt + API + MCP + DSP, 0 warnings enforced)
uv run pytest tests/test_script_service.py -k render
uv run python scripts/build.py                    # Build standalone PyInstaller bundle into dist/VoxLabs/
docker build -t voxlabs-api --build-arg EXTRAS="piper kokoro" .`}
            </pre>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="rounded-xl border border-border/40 bg-card/50 p-5 space-y-2">
                <h3 className="font-semibold text-base">Adding a Feature</h3>
                <ol className="list-decimal list-inside space-y-1 text-muted-foreground leading-relaxed">
                  <li>Put logic in the service, validate with <code>Validation</code>, raise <code>AppError</code> subclasses, and wrap in <code>service_error()</code>.</li>
                  <li>Wrap multi-row writes in one <code>with transaction() as session:</code> block.</li>
                  <li>Add a <code>*_async</code> wrapper using <code>job_service.submit()</code> for slow operations.</li>
                  <li>Wire to UI via <code>BasePage.run()</code> / <code>follow()</code>, REST via <code>app/api/routes/</code> returning <code>ApiResponse(data).success()</code>, and MCP via <code>app/api/mcp/tools.py</code>.</li>
                </ol>
              </div>
              <div className="rounded-xl border border-border/40 bg-card/50 p-5 space-y-2">
                <h3 className="font-semibold text-base">Adding a Model Engine</h3>
                <ol className="list-decimal list-inside space-y-1 text-muted-foreground leading-relaxed">
                  <li>Add an entry to <code>MODEL_CATALOG</code> in <code>app/constants/models.py</code> (with direct Hugging Face <code>files</code> URLs if applicable).</li>
                  <li>Subclass <code>ModelBackend</code> in <code>app/utils/model.py</code> (lazy import inside <code>load()</code>, implement <code>synthesize()</code>).</li>
                  <li>Register the class in <code>_BACKENDS</code>.</li>
                  <li>Add the optional dependency extra in <code>pyproject.toml</code> and run <code>uv lock</code>.</li>
                </ol>
              </div>
            </div>

            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-6 space-y-3">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                Safety &amp; Privacy Guarantees
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Processing is local-first. Voice samples are never silently uploaded to external servers, online engines are opt-in only, every generated file is tagged <code>AI-generated by VoxLabs</code>, and revoking consent deletes voice data immediately. Read our{" "}
                <Link href="/legal/privacy" className="text-foreground underline underline-offset-4">Privacy Policy</Link>
                {" "}and{" "}
                <Link href="/legal/ethics" className="text-foreground underline underline-offset-4">Ethical AI Guidelines</Link>.
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
