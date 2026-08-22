"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Voice } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PlayCircle, CheckCircle2, Bot, Mic, Cpu } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

export default function LibraryPage() {
    const [voices, setVoices] = useState<Voice[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeVoiceId, setActiveVoiceId] = useState<string | null>(null);
    const [selectedModel, setSelectedModel] = useState<string>("standard");

    useEffect(() => {
        loadVoices();
        // Mock loading active voice from local storage
        const saved = localStorage.getItem("voxlabs_active_voice");
        if (saved) setActiveVoiceId(saved);
        const savedModel = localStorage.getItem("voxlabs_active_model");
        if (savedModel) setSelectedModel(savedModel);
    }, []);

    const loadVoices = async () => {
        try {
            setLoading(true);
            const response = await api.voices.list();
            setVoices(response.voices);
        } catch (error) {
            toast.error("Failed to load voices");
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleUseVoice = (voiceId: string) => {
        setActiveVoiceId(voiceId);
        localStorage.setItem("voxlabs_active_voice", voiceId);
        toast.success("Voice selected!");
    };

    const handleModelChange = (val: string) => {
        setSelectedModel(val);
        localStorage.setItem("voxlabs_active_model", val);
        toast.success(`Model updated to ${val === "perfect_clone" ? "Perfect Clone Engine" : "Standard"}`);
    };

    return (
        <div className="container mx-auto py-10 px-4 space-y-8 max-w-7xl">
            <div>
                <h1 className="text-4xl font-bold tracking-tight mb-2">Voice Library</h1>
                <p className="text-muted-foreground">Manage your cloned voices and select text-to-speech models.</p>
            </div>

            {/* Model Selection Section */}
            <section>
                <Card className="bg-muted/50 border-primary/20">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Cpu className="h-5 w-5 text-primary" />
                            Synthesis Engine (Model)
                        </CardTitle>
                        <CardDescription>
                            Select the underlying AI model used for text-to-speech generation.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Select value={selectedModel} onValueChange={handleModelChange}>
                            <SelectTrigger className="w-[300px]">
                                <SelectValue placeholder="Select a model" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="standard">
                                    <div className="flex items-center gap-2">
                                        <Bot className="h-4 w-4" />
                                        <span>Standard (Fast & Reliable)</span>
                                    </div>
                                </SelectItem>
                                <SelectItem value="perfect_clone">
                                    <div className="flex items-center gap-2">
                                        <Mic className="h-4 w-4 text-purple-500" />
                                        <span className="font-medium text-purple-500">Perfect Clone Engine</span>
                                    </div>
                                </SelectItem>
                            </SelectContent>
                        </Select>
                        {selectedModel === "perfect_clone" && (
                            <p className="text-sm text-muted-foreground mt-3 bg-purple-500/10 p-3 rounded-md border border-purple-500/20">
                                Perfect Clone mode attempts to do zero-shot voice cloning for maximum fidelity using advanced neural networks.
                            </p>
                        )}
                    </CardContent>
                </Card>
            </section>

            {/* Voices Grid */}
            <section>
                <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
                    Available Voices
                    <Badge variant="secondary" className="rounded-full">{voices.length}</Badge>
                </h2>

                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3].map(i => (
                            <Card key={i} className="animate-pulse h-[200px]"></Card>
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {voices.map((voice) => (
                            <Card 
                                key={voice.voice_id} 
                                className={`flex flex-col transition-all hover:shadow-md ${activeVoiceId === voice.voice_id ? 'ring-2 ring-primary border-primary' : ''}`}
                            >
                                <CardHeader className="pb-3">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <CardTitle className="text-lg">{voice.name}</CardTitle>
                                            <CardDescription className="text-xs mt-1 font-mono">
                                                ID: {voice.voice_id.substring(0, 8)}...
                                            </CardDescription>
                                        </div>
                                        {voice.voice_id.includes("default") ? (
                                            <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/20">Default</Badge>
                                        ) : (
                                            <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">Cloned</Badge>
                                        )}
                                    </div>
                                </CardHeader>
                                
                                <CardContent className="flex-grow pb-3">
                                    {!voice.voice_id.includes("default") && (
                                        <div className="mt-2 space-y-2">
                                            <p className="text-xs text-muted-foreground font-medium">Source Audio:</p>
                                            <audio 
                                                controls 
                                                className="w-full h-10 rounded-md" 
                                                src={api.voices.sourceUrl(voice.voice_id)}
                                                preload="none"
                                            />
                                        </div>
                                    )}
                                    {voice.voice_id.includes("default") && (
                                        <div className="mt-2 flex items-center justify-center h-10 bg-muted/30 rounded-md text-xs text-muted-foreground italic">
                                            Pre-trained base voice
                                        </div>
                                    )}
                                </CardContent>
                                
                                <CardFooter className="pt-2 border-t mt-auto">
                                    <Button 
                                        variant={activeVoiceId === voice.voice_id ? "default" : "outline"} 
                                        className="w-full gap-2"
                                        onClick={() => handleUseVoice(voice.voice_id)}
                                    >
                                        {activeVoiceId === voice.voice_id ? (
                                            <>
                                                <CheckCircle2 className="h-4 w-4" />
                                                Active Voice
                                            </>
                                        ) : (
                                            "Use Voice"
                                        )}
                                    </Button>
                                </CardFooter>
                            </Card>
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
}
