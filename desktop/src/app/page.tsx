"use client";

import { useEffect, useState } from "react";
import { api, SystemStatus } from "@/lib/api";
import { Card, SectionHeader } from "@/components/ui";

export default function DashboardPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [voiceCount, setVoiceCount] = useState<number | null>(null);

  useEffect(() => {
    api
      .getStatus()
      .then(setStatus)
      .catch((e) => setStatusError(e.message));

    api
      .listVoices()
      .then((data) => setVoiceCount(data.count))
      .catch(() => setVoiceCount(null));
  }, []);

  return (
    <div className="flex max-w-4xl flex-col gap-6">
      <SectionHeader title="Dashboard" subtitle="System status and capabilities at a glance." />

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <p className="text-sm text-foreground-dim">Backend</p>
          <p
            className={`mt-1 text-xl font-semibold ${
              statusError ? "text-danger" : status ? "text-success" : ""
            }`}
          >
            {statusError ? "Offline" : status ? "Connected" : "Checking…"}
          </p>
        </Card>

        <Card>
          <p className="text-sm text-foreground-dim">API Version</p>
          <p className="mt-1 text-xl font-semibold">{status?.version ?? "—"}</p>
        </Card>

        <Card>
          <p className="text-sm text-foreground-dim">Registered Voices</p>
          <p className="mt-1 text-xl font-semibold">{voiceCount ?? "—"}</p>
        </Card>

        <Card className="col-span-3">
          <p className="text-sm text-foreground-dim">Capabilities</p>
          <p className="mt-1 text-xl font-semibold break-words">
            {statusError ? statusError : status?.capabilities.join(", ") || "—"}
          </p>
        </Card>
      </div>
    </div>
  );
}
