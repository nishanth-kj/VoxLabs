"use client"

import { useSyncExternalStore } from "react"
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

// The platform never changes while the page is open, so there is nothing to subscribe to.
const subscribe = () => () => {}

/** The visitor's platform; "unknown" during server rendering and hydration. */
export function usePlatform(): DetectedPlatform {
  return useSyncExternalStore(subscribe, detectPlatform, () => "unknown")
}
