import { Mic, Settings, Activity, FileAudio } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
    isConnected: boolean;
}

export function Sidebar({ activeTab, onTabChange, isConnected }: SidebarProps) {
    return (
        <aside className="w-64 bg-card border-r border-border flex flex-col p-6 h-full">
            <div className="flex items-center gap-3 mb-8 text-xl font-bold text-primary">
                <Activity className="text-accent w-6 h-6" />
                <span>VoxLabs</span>
            </div>

            <nav className="flex-1 space-y-2">
                <button
                    onClick={() => onTabChange('voice-cloning')}
                    className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                        activeTab === 'voice-cloning'
                            ? "bg-accent/10 text-accent"
                            : "text-secondary hover:bg-white/5 hover:text-primary"
                    )}
                >
                    <FileAudio className="w-5 h-5" />
                    Voice Cloning
                </button>
                <button
                    onClick={() => onTabChange('tts')}
                    className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                        activeTab === 'tts'
                            ? "bg-accent/10 text-accent"
                            : "text-secondary hover:bg-white/5 hover:text-primary"
                    )}
                >
                    <Mic className="w-5 h-5" />
                    Text to Speech
                </button>
                <button
                    onClick={() => onTabChange('settings')}
                    className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                        activeTab === 'settings'
                            ? "bg-accent/10 text-accent"
                            : "text-secondary hover:bg-white/5 hover:text-primary"
                    )}
                >
                    <Settings className="w-5 h-5" />
                    Settings
                </button>
            </nav>

            <div className="pt-4 border-t border-border mt-auto">
                <div className="flex items-center gap-2 text-xs text-secondary">
                    <div className={cn(
                        "w-2 h-2 rounded-full",
                        isConnected ? "bg-success" : "bg-warning"
                    )} />
                    {isConnected ? "Connected" : "Connecting..."}
                </div>
            </div>
        </aside>
    );
}
