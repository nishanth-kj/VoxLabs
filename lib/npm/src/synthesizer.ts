import type { VoxLabsConfig } from './index';

export interface TTSRequest {
    text: string;
    voice?: string;
    speed?: number;
    pitch?: number;
    energy?: number;
}

export class VoiceSynthesizer {
    private config: VoxLabsConfig;
    private synth?: SpeechSynthesis;

    constructor(config: VoxLabsConfig = {}) {
        this.config = {
            offline: true,
            watermark: true,
            ...config
        };

        if (typeof window !== 'undefined') {
            this.synth = window.speechSynthesis;
        }
    }

    async synthesize(request: TTSRequest): Promise<HTMLAudioElement> {
        const { text, speed = 1.0, pitch = 1.0, energy = 1.0 } = request;

        if (this.config.offline && this.synth) {
            return this.synthesizeOffline(text, speed, pitch, energy);
        }

        // Fallback to API
        return this.synthesizeAPI(request);
    }

    private synthesizeOffline(
        text: string,
        speed: number,
        pitch: number,
        energy: number
    ): Promise<HTMLAudioElement> {
        return new Promise((resolve, reject) => {
            if (!this.synth) {
                reject(new Error('Speech synthesis not available'));
                return;
            }

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = speed;
            utterance.pitch = pitch;
            utterance.volume = energy;

            utterance.onend = () => {
                const audio = new Audio();
                resolve(audio);
            };

            utterance.onerror = (error) => {
                reject(error);
            };

            this.synth.speak(utterance);
        });
    }

    private async synthesizeAPI(request: TTSRequest): Promise<HTMLAudioElement> {
        const response = await fetch(`${this.config.apiUrl}/api/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });

        const data = await response.json();
        const audio = new Audio(data.audioUrl);
        return audio;
    }

    getVoices(): SpeechSynthesisVoice[] {
        return this.synth?.getVoices() || [];
    }
}
