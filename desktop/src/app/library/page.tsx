"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, Voice } from "@/lib/api";
import { IconLibrary, IconPlus, IconRefresh, IconSearch, IconTrash } from "@/components/icons";
import { Banner, Button, Card, EmptyState, Input, Page, SectionHeader, SpinnerButton } from "@/components/ui";

export default function LibraryPage() {
  const router = useRouter();
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [revoking, setRevoking] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

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

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return voices;
    return voices.filter((voice) => {
      const hay = `${voice.name} ${voice.voice_id} ${voice.project_id ?? "default"}`.toLowerCase();
      return hay.includes(q);
    });
  }, [voices, query]);

  async function revoke(voiceId: string) {
    setRevoking(true);
    try {
      await api.revokeVoice(voiceId);
      setNotice("Voice revoked and removed from this machine.");
      setConfirmId(null);
      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRevoking(false);
    }
  }

  return (
    <Page>
      <SectionHeader
        kicker="Voices"
        title="Voice library"
        subtitle="Voices registered for cloning on this machine. Revoke any voice to delete it completely."
        actions={
          <>
            <Button onClick={refresh} disabled={loading}>
              <IconRefresh className="h-3.5 w-3.5" />
              Refresh
            </Button>
            <Button variant="primary" onClick={() => router.push("/clone")}>
              <IconPlus className="h-3.5 w-3.5" />
              Clone voice
            </Button>
          </>
        }
      />

      {notice && (
        <Banner tone="success" onDismiss={() => setNotice(null)}>
          {notice}
        </Banner>
      )}
      {error && (
        <Banner tone="error" onDismiss={() => setError(null)}>
          {error}
        </Banner>
      )}

      <div className="relative max-w-sm">
        <IconSearch className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-foreground-dim" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search name, ID, or project"
          className="pl-9"
        />
      </div>

      <Card className="overflow-hidden p-0">
        {loading && (
          <ul className="divide-y divide-border">
            {[0, 1, 2].map((i) => (
              <li key={i} className="flex items-center gap-4 px-5 py-3.5">
                <div className="h-9 w-9 animate-pulse rounded-lg bg-surface-alt" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 w-36 animate-pulse rounded bg-surface-alt" />
                  <div className="h-2.5 w-52 animate-pulse rounded bg-surface-alt" />
                </div>
              </li>
            ))}
          </ul>
        )}
        {!loading && filtered.length === 0 && (
          <EmptyState
            icon={<IconLibrary className="h-5 w-5" />}
            title={voices.length === 0 ? "No voices yet" : "No matches"}
            description={
              voices.length === 0
                ? "Clone a consented audio sample or design a voice from a prompt."
                : "Try a different search."
            }
            action={
              voices.length === 0 ? (
                <Button variant="primary" onClick={() => router.push("/clone")}>
                  <IconPlus className="h-3.5 w-3.5" />
                  Clone a voice
                </Button>
              ) : undefined
            }
          />
        )}
        {!loading && filtered.length > 0 && (
          <ul className="divide-y divide-border">
            {filtered.map((voice) => {
              const confirming = confirmId === voice.voice_id;
              return (
                <li key={voice.voice_id} className="flex items-center gap-4 px-5 py-3.5">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-xs font-semibold text-accent-hover">
                    {initials(voice.name)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{voice.name}</p>
                    <p className="truncate font-mono text-[11px] text-foreground-dim">{voice.voice_id}</p>
                  </div>
                  <span className="hidden rounded-full border border-border bg-surface-alt px-2.5 py-0.5 text-[11px] text-foreground-dim sm:inline">
                    {voice.project_id ?? "default"}
                  </span>
                  {confirming ? (
                    <div className="flex items-center gap-2">
                      <Button size="sm" onClick={() => setConfirmId(null)} disabled={revoking}>
                        Cancel
                      </Button>
                      <SpinnerButton
                        size="sm"
                        variant="danger"
                        busy={revoking}
                        onClick={() => revoke(voice.voice_id)}
                      >
                        Confirm revoke
                      </SpinnerButton>
                    </div>
                  ) : (
                    <Button size="sm" variant="ghost" onClick={() => setConfirmId(voice.voice_id)}>
                      <IconTrash className="h-3.5 w-3.5" />
                      Revoke
                    </Button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </Page>
  );
}

function initials(name: string) {
  return (
    name
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? "")
      .join("") || "V"
  );
}
