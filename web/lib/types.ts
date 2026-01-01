
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


export interface ApiResponse<T> {
    status: number;
    data: T;
    error?: string;
}

export interface SynthesisResponse {
    audio_url?: string;
    engine?: string;
    emotion?: string;
    message?: string;
}

export interface CloneRequest {
    voice_name: string;
    audio_file: File;
    description?: string;
}
