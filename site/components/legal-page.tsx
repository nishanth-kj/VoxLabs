import type { ReactNode } from "react"

export function LegalPage({
  title,
  icon,
  children,
}: {
  title: string
  icon?: ReactNode
  children: ReactNode
}) {
  return (
    <div className="min-h-screen bg-background text-foreground pt-12 pb-20 px-6">
      <article className="max-w-3xl mx-auto space-y-8">
        <header className="flex items-center gap-3 mb-2">
          {icon}
          <h1 className="text-4xl font-bold tracking-tight">{title}</h1>
        </header>
        <div className="space-y-6 text-muted-foreground leading-relaxed [&_h2]:text-foreground [&_h2]:text-2xl [&_h2]:font-semibold [&_h2]:mt-10 [&_h2]:mb-3 [&_h3]:text-foreground [&_h3]:text-lg [&_h3]:font-semibold [&_h3]:mt-6 [&_h3]:mb-2 [&_ul]:list-disc [&_ul]:pl-6 [&_ul]:space-y-2 [&_a]:text-foreground [&_a]:underline [&_a]:underline-offset-4">
          {children}
        </div>
      </article>
    </div>
  )
}
