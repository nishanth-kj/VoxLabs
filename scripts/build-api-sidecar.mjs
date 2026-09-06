#!/usr/bin/env node
// Bundles api/main.py into a standalone executable via PyInstaller, then copies it
// into desktop/src-tauri/binaries with the platform target-triple suffix Tauri's
// sidecar mechanism requires. Run via `npm run build:api` (also runs automatically
// before `npm run build:desktop`).

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, copyFileSync, rmSync } from "node:fs";
import { platform } from "node:os";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const apiDir = path.join(root, "api");
const binariesDir = path.join(root, "desktop", "src-tauri", "binaries");
const dataSep = platform() === "win32" ? ";" : ":";
const exeSuffix = platform() === "win32" ? ".exe" : "";

function run(commandLine, opts = {}) {
  console.log(`\n> ${commandLine}${opts.cwd ? `  (in ${opts.cwd})` : ""}`);
  const result = spawnSync(commandLine, { shell: true, stdio: "inherit", ...opts });
  if (result.status !== 0) {
    throw new Error(`Command failed (exit ${result.status}): ${commandLine}`);
  }
}

function captureRun(commandLine, opts = {}) {
  const result = spawnSync(commandLine, { shell: true, encoding: "utf8", ...opts });
  if (result.status !== 0) {
    throw new Error(`Command failed (exit ${result.status}): ${commandLine}\n${result.stderr}`);
  }
  return result.stdout;
}

/** Tauri names sidecars "<name>-<rust-host-triple>[.exe]" - ask rustc what that is. */
function getHostTriple() {
  const output = captureRun("rustc -vV");
  const match = output.match(/host:\s*(\S+)/);
  if (!match) {
    throw new Error("Could not determine host triple from `rustc -vV` - is Rust installed?");
  }
  return match[1];
}

console.log("== Building VoxLabs API sidecar ==");

rmSync(path.join(apiDir, "build"), { recursive: true, force: true });
rmSync(path.join(apiDir, "dist"), { recursive: true, force: true });

run(
  [
    "uv run pyinstaller",
    "--name voxlabs-api",
    "--onefile",
    "--noconfirm",
    `--add-data static${dataSep}static`,
    `--add-data database/migrations${dataSep}database/migrations`,
    "--collect-all librosa",
    "--collect-all numba",
    "--collect-all soundfile",
    "--collect-all edge_tts",
    "--collect-submodules uvicorn",
    "main.py",
  ].join(" "),
  { cwd: apiDir }
);

const builtExe = path.join(apiDir, "dist", `voxlabs-api${exeSuffix}`);
if (!existsSync(builtExe)) {
  throw new Error(`PyInstaller did not produce the expected binary at ${builtExe}`);
}

mkdirSync(binariesDir, { recursive: true });
const triple = getHostTriple();
const sidecarPath = path.join(binariesDir, `voxlabs-api-${triple}${exeSuffix}`);
copyFileSync(builtExe, sidecarPath);

console.log(`\nSidecar ready: ${sidecarPath}`);
