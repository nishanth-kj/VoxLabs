
export interface Voice {
    id: string;
    name: string;
    description?: string;
    projectId?: string;
}

export interface Emotion {
    name: string;
    value: string;
}

export interface SynthesisRequest {
    text: string;
    engine?: string;
    voice_id?: string;
    language?: string;
    emotion?: string;
    speed?: number;
    pitch?: number;
    energy?: number;
}

export interface SynthesisResponse {
    success: boolean;
    audio_url?: string;
    detail?: string;
}

export interface CloneRequest {
    voice_name: string;
    audio_file: File;
    description?: string;
}
