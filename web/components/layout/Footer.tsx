import { AudioWaveform } from 'lucide-react'

export function Footer() {
    return (
        <footer className="border-t border-white/5 bg-background/50 backdrop-blur-sm mt-auto">
            <div className="max-w-7xl mx-auto px-6 py-12">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
                    <div className="md:col-span-2 space-y-4">
                        <div className="flex items-center gap-2">
                            <div className="h-6 w-6 rounded bg-indigo-500/20 flex items-center justify-center">
                                <AudioWaveform className="h-3 w-3 text-indigo-400" />
                            </div>
                            <span className="font-bold text-base">VoxLabs</span>
                        </div>
                        <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">
                            Pioneering the future of voice technology with ethical AI cloning and emotionally resonant speech synthesis.
                        </p>
                    </div>
                    <div>
                        <h4 className="font-semibold text-sm mb-4">Community</h4>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <a href="/contribution">Contribution</a>
                            </li>
                            <li className="hover:text-primary cursor-pointer transition-colors">
                                <a href="https://github.com/nishanth-kj/Text-to-Speech" target="_blank">GitHub</a>
                            </li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="font-semibold text-sm mb-4">Legal</h4>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                            <li className="hover:text-primary cursor-pointer transition-colors">Privacy Policy</li>
                            <li className="hover:text-primary cursor-pointer transition-colors">Terms of Service</li>
                            <li className="hover:text-primary cursor-pointer transition-colors">Ethical AI Guidelines</li>
                        </ul>
                    </div>
                </div>
                <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-muted-foreground">
                    <p>&copy; {new Date().getFullYear()} VoxLabs AI. All rights reserved.</p>
                    <p>Built with Next.js & FastAPI.</p>
                </div>
            </div>
        </footer>
    )
}
