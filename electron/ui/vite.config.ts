import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    base: './', // Crucial for Electron file:// protocol
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    build: {
        outDir: '../renderer-dist', // Build to a folder that electron-builder won't wipe
        emptyOutDir: true,
    }
})
