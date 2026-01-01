# Frontend Documentation

The VoxLabs frontend is a modern web application known as the **Studio**. It provides an intuitive interface for synthesis and voice cloning.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn UI (Radix Primitives)
- **Animations**: GSAP (GreenSock) & Framer Motion
- **Icons**: Lucide React

## Architecture

### `web/app/studio/page.tsx`
This is the main interaction hub. It handles:
1.  **State Management**:
    - `text`: Input text for synthesis.
    - `selectedEmotion`: Drives the UI sliders via `useEffect`.
    - `voices`: List of available voices fetched from API.
2.  **UI Sync**:
    - Listens for changes in `selectedEmotion`.
    - Automatically updates `speed`, `pitch`, and `energy` sliders to match backend defaults.
3.  **Visualization**:
    - Simple audio waveform visualization using CSS animations.

### API Client (`web/lib/api.ts`)
A centralized HTTP client wrapper around `fetch`.
- **Response Handling**: Automatically unwraps the `{ status, data, error }` format.
    - Throws an error if `status === 0`.
    - Returns `data` if `status === 1`.
- **Type Safety**: Uses TypeScript interfaces from `types.ts` to ensure type verification at compile time.

## Desktop Application (Tauri)
The `desktop/` directory allows bundling this frontend as a native app.
- It loads the Next.js static export or local server.
- Provides native window controls and OS integration.
