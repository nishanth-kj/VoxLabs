import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'VoxLabs - AI Voice Cloning Platform',
  description: 'Professional voice cloning and text-to-speech with ethical AI practices',
  keywords: ['voice cloning', 'TTS', 'AI', 'speech synthesis', 'ethical AI'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
