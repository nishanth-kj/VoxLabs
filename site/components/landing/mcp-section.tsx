import { Bot, ListChecks, Plug, ShieldCheck } from "lucide-react"
import type { ReactNode } from "react"

import { GITHUB_URL } from "@/lib/links"

export const MCP_DESKTOP_CONFIG = `{
  "mcpServers": {
    "voxlabs": {
      "command": "C:\\\\Program Files\\\\VoxLabs\\\\VoxLabs.exe",
      "args": ["--mcp"]
    }
  }
}`

export const MCP_CLAUDE_CODE = "claude mcp add voxlabs -- uv run --directory /path/to/VoxLabs voxlabs-mcp"

export function McpSection() {
  return (
    <section id="mcp" className="py-20 px-6 bg-secondary/30 border-t border-border/40">
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
        <div className="space-y-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-purple-500/10 border border-purple-500/20">
            <Bot className="w-7 h-7 text-purple-500" />
          </div>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Works with Your AI Apps</h2>
          <p className="text-muted-foreground text-lg leading-relaxed">
            VoxLabs is an MCP server. Claude Desktop, Claude Code and other MCP clients can generate speech, build and
            render scripts, process and export audio, browse your files and manage models, using the same features as
            the desktop app.
          </p>
          <ul className="space-y-4">
            <Point icon={<Plug className="w-5 h-5 text-indigo-400" />} title="No window, no port">
              Your AI app starts VoxLabs by itself (<code className="font-mono text-xs">VoxLabs --mcp</code>), so the
              desktop app doesn&apos;t need to be open. A local HTTP endpoint is there too.
            </Point>
            <Point icon={<ListChecks className="w-5 h-5 text-emerald-400" />} title="Every call is logged">
              The MCP page shows each call live, with its arguments, result or error and duration, plus all 30 tools and
              the ready-to-paste configuration for your install.
            </Point>
            <Point icon={<ShieldCheck className="w-5 h-5 text-pink-400" />} title="Consent stays human">
              Voice cloning is never offered to agents. Consent has to come from the speaker in the desktop app.
            </Point>
          </ul>
        </div>

        <div className="space-y-6">
          <Snippet title="Claude Desktop · claude_desktop_config.json" code={MCP_DESKTOP_CONFIG} />
          <Snippet title="Claude Code · from source" code={MCP_CLAUDE_CODE} />
          <p className="text-sm text-muted-foreground">
            The MCP page in VoxLabs shows these with the paths of your own install and a Copy button.{" "}
            <a href={`${GITHUB_URL}/blob/main/docs/rest-api.md#mcp-server`}
               className="underline underline-offset-4 hover:text-foreground">
              MCP documentation
            </a>
          </p>
        </div>
      </div>
    </section>
  )
}

function Point({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <li className="flex gap-4">
      <div className="mt-1 shrink-0">{icon}</div>
      <div>
        <p className="font-semibold">{title}</p>
        <p className="text-sm text-muted-foreground leading-relaxed">{children}</p>
      </div>
    </li>
  )
}

function Snippet({ title, code }: { title: string; code: string }) {
  return (
    <div className="rounded-xl border border-border/50 bg-card/70 shadow-sm overflow-hidden">
      <div className="px-4 py-2 border-b border-border/40 text-xs font-medium text-muted-foreground">{title}</div>
      <pre className="p-4 text-xs sm:text-sm font-mono overflow-x-auto leading-relaxed"><code>{code}</code></pre>
    </div>
  )
}
