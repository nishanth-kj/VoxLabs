import React, { useState } from 'react';
import { Upload, Mic, Loader2, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VoiceCloningViewProps {
    apiUrl: string;
}

export function VoiceCloningView({ apiUrl }: VoiceCloningViewProps) {
    const [name, setName] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
    const [errorMsg, setErrorMsg] = useState('');

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file || !name) return;

        setIsUploading(true);
        setErrorMsg('');

        try {
            const formData = new FormData();
            formData.append('name', name);
            formData.append('file', file);
            // Ensure we explicitly verify the endpoint in the new API setup
            const response = await fetch(`${apiUrl}/api/voices/register`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (result.status === 1) {
                setStatus('success');
                setName('');
                setFile(null);
                setTimeout(() => setStatus('idle'), 3000);
            } else {
                throw new Error(result.error || 'Unknown error');
            }
        } catch (err: any) {
            console.error(err);
            setStatus('error');
            setErrorMsg(err.message || 'Failed to upload');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto pt-10">
            <header className="mb-8">
                <h1 className="text-3xl font-bold mb-2">Voice Cloning</h1>
                <p className="text-secondary">Create a custom voice model from a short audio sample.</p>
            </header>

            <div className="bg-card border border-border rounded-xl p-8">
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-secondary">Voice Name</label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="e.g. My Narrator Voice"
                            className="w-full bg-black/20 border border-border rounded-lg px-4 py-3 text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-secondary">Reference Audio</label>
                        <div
                            onDragOver={(e) => e.preventDefault()}
                            onDrop={handleDrop}
                            className="border-2 border-dashed border-border rounded-xl p-8 text-center hover:bg-accent/5 hover:border-accent transition-colors cursor-pointer group"
                            onClick={() => document.getElementById('audio-upload')?.click()}
                        >
                            <input
                                id="audio-upload"
                                type="file"
                                accept="audio/*"
                                onChange={handleFileChange}
                                className="hidden"
                            />
                            <div className="flex flex-col items-center gap-3">
                                <div className="w-12 h-12 rounded-full bg-border flex items-center justify-center group-hover:bg-accent/10 transition-colors">
                                    <Upload className="w-6 h-6 text-secondary group-hover:text-accent" />
                                </div>
                                <div className="space-y-1">
                                    <p className="font-medium text-primary">
                                        {file ? file.name : "Click or drag to upload audio"}
                                    </p>
                                    <p className="text-xs text-secondary">WAV or MP3 (1-5 mins)</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {status === 'error' && (
                        <div className="p-3 bg-danger/10 text-danger text-sm rounded-lg">
                            Error: {errorMsg}
                        </div>
                    )}

                    {status === 'success' && (
                        <div className="p-3 bg-success/10 text-success text-sm rounded-lg flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4" />
                            Voice cloned successfully!
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isUploading}
                        className={cn(
                            "w-full flex items-center justify-center gap-2 py-3 rounded-lg font-semibold transition-all",
                            isUploading
                                ? "bg-accent/50 cursor-not-allowed"
                                : "bg-accent hover:bg-accent-hover active:scale-[0.98]"
                        )}
                    >
                        {isUploading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Cloning...
                            </>
                        ) : (
                            <>
                                <Mic className="w-5 h-5" />
                                Create Voice Clone
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
