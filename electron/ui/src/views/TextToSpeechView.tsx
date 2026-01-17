import { useState } from 'react';
import { Play, Loader2, Download } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TextToSpeechViewProps {
    apiUrl: string;
}

export function TextToSpeechView({ apiUrl }: TextToSpeechViewProps) {
    const [text, setText] = useState('');
    const [selectedVoice, setSelectedVoice] = useState('default');
    const [isGenerating, setIsGenerating] = useState(false);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);

    // Mock voices for now, ideally fetch from API
    const voices = [
        { id: 'default', name: 'Default Voice' },
        { id: 'cloned-1', name: 'Cloned Voice 1' }
    ];

    const handleGenerate = async () => {
        if (!text) return;
        setIsGenerating(true);
        setAudioUrl(null);

        try {
            const response = await fetch(`${apiUrl}/api/tts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, voice_id: selectedVoice })
            });

            if (!response.ok) throw new Error('Generation failed');

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            setAudioUrl(url);
        } catch (error) {
            console.error(error);
            alert('Failed to generate audio. Ensure backend is running.');
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto pt-10 px-4">
            <header className="mb-8">
                <h1 className="text-3xl font-bold mb-2 text-primary">Text to Speech</h1>
                <p className="text-secondary">Generate lifelike speech from text using AI voices.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Inputs */}
                <div className="md:col-span-2 space-y-6">
                    <div className="bg-card border border-border rounded-xl p-6">
                        <label className="block text-sm font-medium text-secondary mb-2">Input Text</label>
                        <textarea
                            className="w-full bg-black/20 border border-border rounded-lg p-4 text-primary focus:outline-none focus:ring-2 focus:ring-accent min-h-[200px] resize-none"
                            placeholder="Type something to generate speech..."
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                        />
                        <div className="flex justify-between items-center mt-4">
                            <span className="text-xs text-secondary">{text.length} characters</span>
                            <button
                                onClick={handleGenerate}
                                disabled={!text || isGenerating}
                                className={cn(
                                    "bg-accent hover:bg-accent-hover text-white px-6 py-2 rounded-lg font-medium transition-all flex items-center gap-2",
                                    (!text || isGenerating) && "opacity-50 cursor-not-allowed"
                                )}
                            >
                                {isGenerating ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Generating...
                                    </>
                                ) : (
                                    <>
                                        <Play className="w-4 h-4 fill-current" />
                                        Generate Audio
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Settings & Output */}
                <div className="space-y-6">
                    <div className="bg-card border border-border rounded-xl p-6">
                        <label className="block text-sm font-medium text-secondary mb-3">Voice Selection</label>
                        <div className="space-y-2">
                            {voices.map(voice => (
                                <button
                                    key={voice.id}
                                    onClick={() => setSelectedVoice(voice.id)}
                                    className={cn(
                                        "w-full text-left px-4 py-3 rounded-lg text-sm transition-colors border",
                                        selectedVoice === voice.id
                                            ? "border-accent bg-accent/10 text-accent"
                                            : "border-border text-secondary hover:border-primary/50 hover:text-primary"
                                    )}
                                >
                                    {voice.name}
                                </button>
                            ))}
                        </div>
                    </div>

                    {audioUrl && (
                        <div className="bg-card border border-border rounded-xl p-6 animate-in fade-in slide-in-from-bottom-4">
                            <label className="block text-sm font-medium text-secondary mb-3">Generated Audio</label>
                            <audio controls src={audioUrl} className="w-full mb-4" />
                            <a
                                href={audioUrl}
                                download="generated_speech.wav"
                                className="w-full flex items-center justify-center gap-2 bg-secondary/10 hover:bg-secondary/20 text-primary py-2 rounded-lg text-sm font-medium transition-colors"
                            >
                                <Download className="w-4 h-4" />
                                Download
                            </a>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
