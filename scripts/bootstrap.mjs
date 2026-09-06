#!/usr/bin/env node
// Runs automatically after `npm install` at the repo root (see package.json "postinstall").
// Checks for the toolchains VoxLabs needs and installs whatever is missing, then
// installs the Python and desktop-app dependencies. Safe to re-run any time.

import { spawnSync } from "node:child_process";
import { homedir, platform } from "node:os";
import { existsSync } from "node:fs";
import path from "node:path";

const isWindows = platform() === "win32";

function commandExists(cmd, versionFlag = "--version") {
  const result = spawnSync(`${cmd} ${versionFlag}`, { shell: true, stdio: "ignore" });
  return result.status === 0;
}

/** @param {string} commandLine a full shell command line (quoting is the caller's job) */
function run(commandLine, opts = {}) {
  console.log(`\n> ${commandLine}${opts.cwd ? `  (in ${opts.cwd})` : ""}`);
  const result = spawnSync(commandLine, { shell: true, stdio: "inherit", ...opts });
  if (result.status !== 0) {
    throw new Error(`Command failed (exit ${result.status}): ${commandLine}`);
  }
}

// Newly-installed tools won't be on PATH for this already-running process (and in some
// shells not even for the next one, until the terminal is restarted), so also search
// each tool's well-known install location directly.
function extendPathForNewInstalls() {
  const home = homedir();
  const extra = [
    path.join(home, ".local", "bin"),
    path.join(home, ".cargo", "bin"),
    "C:\\Program Files\\ffmpeg\\bin",
  ];
  const sep = isWindows ? ";" : ":";
  process.env.PATH = [...extra, process.env.PATH].join(sep);
}

function ensureUv() {
  extendPathForNewInstalls();
  if (commandExists("uv")) {
    console.log("✓ uv already installed");
    return;
  }
  console.log("✗ uv not found — installing (https://astral.sh/uv)...");
  if (isWindows) {
    run(`powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"`);
  } else {
    run(`curl -LsSf https://astral.sh/uv/install.sh | sh`);
  }
  extendPathForNewInstalls();
  if (!commandExists("uv")) {
    console.warn("uv was installed but isn't on PATH yet — open a new terminal and re-run `npm install`.");
  }
}

function ensureRust() {
  extendPathForNewInstalls();
  if (commandExists("cargo") && commandExists("rustc")) {
    console.log("✓ Rust toolchain already installed");
    return;
  }
  console.log("✗ Rust toolchain not found — installing (https://rustup.rs)...");
  if (isWindows) {
    const rustupInit = path.join(process.env.TEMP || homedir(), "rustup-init.exe");
    run(`powershell -Command "Invoke-WebRequest -Uri https://win.rustup.rs -OutFile '${rustupInit}'"`);
    run(`"${rustupInit}" -y --default-toolchain stable --profile default`);
  } else {
    run(`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y`);
  }
  extendPathForNewInstalls();
  if (!commandExists("cargo")) {
    console.warn("Rust was installed but isn't on PATH yet — open a new terminal and re-run `npm install`.");
  }
}

function ensureFfmpeg() {
  extendPathForNewInstalls();
  if (commandExists("ffmpeg", "-version")) {
    console.log("✓ ffmpeg already installed");
    return;
  }
  console.log("✗ ffmpeg not found — installing...");
  if (isWindows) {
    if (commandExists("winget")) {
      // winget exits non-zero for "already installed, no upgrade available" too —
      // that's not a failure, so don't let it throw; we verify with commandExists below.
      spawnSync(
        `winget install --id Gyan.FFmpeg -e --source winget --accept-package-agreements --accept-source-agreements`,
        { shell: true, stdio: "inherit" }
      );
    } else {
      console.warn("winget not found — install ffmpeg manually: https://ffmpeg.org/download.html");
      return;
    }
  } else if (platform() === "darwin") {
    if (commandExists("brew")) {
      run(`brew install ffmpeg`);
    } else {
      console.warn("Homebrew not found — install ffmpeg manually: https://ffmpeg.org/download.html");
      return;
    }
  } else if (commandExists("apt-get")) {
    run(`sudo apt-get update && sudo apt-get install -y ffmpeg`);
  } else if (commandExists("dnf")) {
    run(`sudo dnf install -y ffmpeg`);
  } else if (commandExists("pacman")) {
    run(`sudo pacman -Sy --noconfirm ffmpeg`);
  } else {
    console.warn("No supported package manager found — install ffmpeg manually: https://ffmpeg.org/download.html");
    return;
  }
  if (!commandExists("ffmpeg", "-version")) {
    console.warn("ffmpeg was installed but isn't on PATH yet — open a new terminal and re-run `npm install`.");
  }
}

const root = path.resolve(import.meta.dirname, "..");

function tryStep(name, fn) {
  try {
    fn();
  } catch (err) {
    console.warn(`⚠ ${name} failed: ${err.message}`);
    console.warn("  Continuing with the rest of setup — fix this manually if you need it.");
  }
}

console.log("== VoxLabs dev environment bootstrap ==");
tryStep("uv install check", ensureUv);
tryStep("Rust install check", ensureRust);
tryStep("ffmpeg install check", ensureFfmpeg);

console.log("\n== Python dependencies (api/) ==");
run("uv sync", { cwd: path.join(root, "api") });

console.log("\n== Desktop app dependencies (desktop/) ==");
if (existsSync(path.join(root, "desktop", "node_modules"))) {
  console.log("✓ desktop/node_modules already present (run `npm install` inside desktop/ if it's stale)");
} else {
  run("npm install", { cwd: path.join(root, "desktop") });
}

console.log("\nAll set. Try: npm run dev");
