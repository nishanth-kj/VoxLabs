"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type StudioModel } from "@/lib/api";
import { IconCpu, IconRefresh, IconSearch } from "@/components/icons";
import { Badge, Banner, Button, Card, EmptyState, Input, Page, SectionHeader } from "@/components/ui";

export default function ModelsPage() {
  const router = useRouter();
  const [engines, setEngines] = useState<StudioModel[]>([]);
  const [voices, setVoices] = useState<StudioModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  const load = useCallback((showSpinner = false) => {
    if (showSpinner) setLoading(true);
    return api
      .listModels()
      .then((data) => {
        setEngines(data.engines);
        setVoices(data.voices);
        setError(null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .listModels()
      .then((data) => {
        if (cancelled) return;
        setEngines(data.engines);
        setVoices(data.voices);
        setError(null);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredVoices = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return voices;
    return voices.filter((voice) => {
      const hay = `${voice.name} ${voice.id} ${voice.locale ?? ""} ${voice.gender ?? ""}`.toLowerCase();
      return hay.includes(q);
    });
  }, [voices, query]);

  return (
    <Page>
      <SectionHeader
        kicker="Catalog"
        title="Models"
        subtitle="Every synthesis engine on this machine, plus Microsoft Edge voice models when reachable."
        actions={
          <Button onClick={() => load(true)} disabled={loading}>
            <IconRefresh className="h-3.5 w-3.5" />
            Refresh
          </Button>
        }
      />

      {error && (
        <Banner tone="error" onDismiss={() => setError(null)}>
          {error}
        </Banner>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        {engines.map((model) => (
          <EngineCard key={model.id} model={model} onOpen={() => openEngine(router, model.id)} />
        ))}
        {!loading && engines.length === 0 && !error && (
          <Card className="lg:col-span-3">
            <EmptyState
              icon={<IconCpu className="h-5 w-5" />}
              title="No engines listed"
              description="The backend did not return any synthesis engines."
            />
          </Card>
        )}
      </div>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-sm font-medium">Edge voice models</h2>
          <p className="mt-0.5 text-xs text-foreground-dim">
            {loading ? "Loading…" : `${filteredVoices.length} of ${voices.length} voices`}
          </p>
        </div>
        <div className="relative w-full max-w-sm">
          <IconSearch className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-foreground-dim" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search name, locale, or gender"
            className="pl-9"
          />
        </div>
      </div>

      <Card className="overflow-hidden p-0">
        {loading && (
          <ul className="divide-y divide-border">
            {[0, 1, 2, 3].map((i) => (
              <li key={i} className="flex items-center gap-4 px-5 py-3.5">
                <div className="h-9 w-9 animate-pulse rounded-lg bg-surface-alt" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 w-48 animate-pulse rounded bg-surface-alt" />
                  <div className="h-2.5 w-32 animate-pulse rounded bg-surface-alt" />
                </div>
              </li>
            ))}
          </ul>
        )}
        {!loading && filteredVoices.length === 0 && (
          <EmptyState
            icon={<IconCpu className="h-5 w-5" />}
            title={voices.length === 0 ? "No Edge voices" : "No matches"}
            description={
              voices.length === 0
                ? "Edge TTS voices appear here when the Microsoft catalog is reachable."
                : "Try a different search."
            }
          />
        )}
        {!loading && filteredVoices.length > 0 && (
          <ul className="divide-y divide-border">
            {filteredVoices.map((voice) => (
              <li key={voice.id} className="flex items-center gap-4 px-5 py-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-500/15 text-xs font-semibold text-violet-300">
                  {(voice.locale ?? "EN").slice(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{voice.name}</p>
                  <p className="truncate font-mono text-[11px] text-foreground-dim">{voice.id}</p>
                </div>
                {voice.locale && (
                  <span className="hidden text-xs text-foreground-dim sm:inline">{voice.locale}</span>
                )}
                {voice.gender && (
                  <Badge className="hidden sm:inline-flex">{voice.gender}</Badge>
                )}
                <Button size="sm" onClick={() => router.push("/studio")}>
                  Use
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </Page>
  );
}

function EngineCard({ model, onOpen }: { model: StudioModel; onOpen: () => void }) {
  const tone = model.status === "available" ? "success" : model.status === "degraded" ? "accent" : "danger";
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{model.name}</p>
          <p className="mt-0.5 text-[11px] text-foreground-dim">
            {model.provider} · {model.offline ? "offline" : "network"}
          </p>
        </div>
        <Badge tone={tone}>{model.status}</Badge>
      </div>
      <p className="text-sm leading-relaxed text-foreground-dim">{model.description}</p>
      {model.note && <p className="text-xs text-danger">{model.note}</p>}
      <div className="flex flex-wrap gap-1.5">
        {(model.capabilities ?? []).map((cap) => (
          <Badge key={cap}>{cap}</Badge>
        ))}
        {typeof model.variant_count === "number" && <Badge tone="accent">{model.variant_count} voices</Badge>}
      </div>
      <Button className="mt-auto self-start" onClick={onOpen}>
        Open
      </Button>
    </Card>
  );
}

function openEngine(router: ReturnType<typeof useRouter>, id: string) {
  if (id === "clone") router.push("/clone");
  else router.push("/studio");
}
