"use client"

import { useEffect, useState } from "react"
import type { PlatformId } from "@/lib/links"

export type DetectedPlatform = PlatformId | "unknown"

export function detectPlatform(): DetectedPlatform {
  if (typeof navigator === "undefined") return "unknown"

  const ua = navigator.userAgent
  const platform = navigator.platform || ""

  if (/Win/i.test(ua) || /Win/i.test(platform)) return "windows"
  if (/Mac/i.test(ua) || /Mac/i.test(platform)) return "macos"
  if (/Linux/i.test(ua) || /Linux/i.test(platform)) return "linux"
  return "unknown"
}

export function usePlatform() {
  const [platform, setPlatform] = useState<DetectedPlatform>("unknown")

  useEffect(() => {
    setPlatform(detectPlatform())
  }, [])

  return platform
}
