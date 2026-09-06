import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { LogsPanel } from "@/components/logs-panel";
import { Navbar } from "@/components/navbar";
import { THEME_BOOTSTRAP } from "@/lib/theme";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "VoxLabs Studio",
  description: "AI voice cloning and text-to-speech studio",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} />
      </head>
      <body className="flex h-screen flex-col overflow-hidden bg-background font-sans text-foreground">
        <Navbar />
        <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">{children}</main>
        <LogsPanel />
      </body>
    </html>
  );
}
