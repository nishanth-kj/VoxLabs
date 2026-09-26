export const GITHUB_URL = "https://github.com/nishanth-kj/VoxLabs"
export const RELEASES_URL = `${GITHUB_URL}/releases/latest`
export const ISSUES_URL = `${GITHUB_URL}/issues`
export const DISCUSSIONS_URL = `${GITHUB_URL}/discussions`

// File names match the release assets built by .github/workflows/desktop.yml.
export const PLATFORMS = [
  {
    id: "windows" as const,
    label: "Windows",
    requirement: "Windows 10 or later",
    fileHint: "VoxLabs-Windows-x64.zip",
    href: RELEASES_URL,
  },
  {
    id: "macos" as const,
    label: "macOS",
    requirement: "macOS 13 (Ventura) or later (Apple silicon)",
    fileHint: "VoxLabs-macOS-arm64.dmg",
    href: RELEASES_URL,
  },
  {
    id: "linux" as const,
    label: "Linux",
    requirement: "Ubuntu 22.04+ / Fedora 39+",
    fileHint: "VoxLabs-Linux-x86_64.tar.gz",
    href: RELEASES_URL,
  },
]

export type PlatformId = (typeof PLATFORMS)[number]["id"]
