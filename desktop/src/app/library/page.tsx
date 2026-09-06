"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, Voice } from "@/lib/api";
import { Button, SectionHeader } from "@/components/ui";

export default function LibraryPage() {
  const router = useRouter();
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const fetchVoices = useCallback(() => {
    return api
      .listVoices()
      .then((data) => {
        setVoices(data.voices);
        setError(null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const refresh = useCallback(() => {
    setLoading(true);
    fetchVoices();
  }, [fetchVoices]);

  useEffect(() => {
    fetchVoices();
  }, [fetchVoices]);

  async function revokeSelected() {
    if (!selected) return;
    const voice = voices.find((v) => v.voice_id === selected);
    if (!confirm(`Permanently revoke '${voice?.name ?? selected}'? This cannot be undone.`)) return;
    try {
      await api.revokeVoice(selected);
      setSelected(null);
      refresh();
    } catch (e) {
      alert((e as Error).message);
    }
  }

  return (
    <div className="flex max-w-4xl flex-col gap-4">
      <div className="flex items-start justify-between">
        <SectionHeader title="Voice Library" subtitle="Voices registered for cloning on this machine." />
        <div className="flex gap-2">
          <Button onClick={refresh}>Refresh</Button>
          <Button variant="primary" onClick={() => router.push("/clone")}>
            + Clone Voice
          </Button>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="bg-surface-alt text-foreground-dim">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Name</th>
              <th className="px-3 py-2 text-left font-medium">Voice ID</th>
              <th className="px-3 py-2 text-left font-medium">Project</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={3} className="px-3 py-6 text-center text-foreground-dim">
                  Loading…
                </td>
              </tr>
            )}
            {!loading && error && (
              <tr>
                <td colSpan={3} className="px-3 py-6 text-center text-danger">
                  {error}
                </td>
              </tr>
            )}
            {!loading && !error && voices.length === 0 && (
              <tr>
                <td colSpan={3} className="px-3 py-6 text-center text-foreground-dim">
                  No voices registered yet.
                </td>
              </tr>
            )}
            {voices.map((voice) => (
              <tr
                key={voice.voice_id}
                onClick={() => setSelected(voice.voice_id)}
                className={`cursor-pointer border-t border-border ${
                  selected === voice.voice_id ? "bg-accent/20" : "hover:bg-surface-alt"
                }`}
              >
                <td className="px-3 py-2">{voice.name}</td>
                <td className="px-3 py-2 text-foreground-dim">{voice.voice_id}</td>
                <td className="px-3 py-2 text-foreground-dim">{voice.project_id ?? "default"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-end">
        <Button variant="danger" disabled={!selected} onClick={revokeSelected}>
          Revoke Selected
        </Button>
      </div>
    </div>
  );
}
