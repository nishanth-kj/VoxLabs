"use client"

import { useState, useSyncExternalStore } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export const COOKIE_NOTICE_KEY = "voxlabs-cookie-notice"

function wasDismissed(): boolean {
  try {
    return window.localStorage.getItem(COOKIE_NOTICE_KEY) === "dismissed"
  } catch {
    return false
  }
}

const subscribe = () => () => {}

export function CookieNotice() {
  // Hidden while server rendering; shown in the browser until it has been dismissed.
  const dismissedBefore = useSyncExternalStore(subscribe, wasDismissed, () => true)
  const [dismissedNow, setDismissedNow] = useState(false)

  function dismiss() {
    try {
      window.localStorage.setItem(COOKIE_NOTICE_KEY, "dismissed")
    } catch {
      // Ignore quota / private-mode failures; the notice can reappear.
    }
    setDismissedNow(true)
  }

  if (dismissedBefore || dismissedNow) return null

  return (
    <div
      role="dialog"
      aria-label="Cookie and privacy notice"
      className="fixed bottom-0 inset-x-0 z-50 border-t border-border/40 bg-background/95 backdrop-blur-md"
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex flex-col sm:flex-row sm:items-center gap-4">
        <p className="text-sm text-muted-foreground leading-relaxed flex-1">
          This site does not use tracking or advertising cookies. Theme preference is stored in your browser.
          Read the{" "}
          <Link href="/legal/cookies" className="underline underline-offset-4 text-foreground">
            cookie policy
          </Link>{" "}
          and{" "}
          <Link href="/legal/privacy" className="underline underline-offset-4 text-foreground">
            privacy policy
          </Link>
          .
        </p>
        <Button size="sm" onClick={dismiss} className="shrink-0">
          OK
        </Button>
      </div>
    </div>
  )
}
