/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#09090b",
                card: "#18181b",
                primary: "#fafafa",
                secondary: "#a1a1aa",
                accent: "#6366f1",
                "accent-hover": "#4f46e5",
                border: "#27272a",
                danger: "#ef4444",
                success: "#22c55e",
                warning: "#eab308",
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            }
        },
    },
    plugins: [],
}
