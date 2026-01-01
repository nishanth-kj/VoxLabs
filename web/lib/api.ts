import { Voice, SynthesisResponse } from './types';

type RequestBody = Record<string, any> | FormData;

class ApiClient {
    private baseUrl: string;

    constructor() {
        this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        if (this.baseUrl.endsWith('/')) {
            this.baseUrl = this.baseUrl.slice(0, -1);
        }
    }

    private async request<T>(method: string, endpoint: string, body?: RequestBody, customHeaders: Record<string, string> = {}): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const headers: Record<string, string> = { ...customHeaders };

        let options: RequestInit = {
            method,
            headers,
        };

        if (body) {
            if (body instanceof FormData) {
                // Content-Type header is automatically set by browser for FormData
                options.body = body;
            } else {
                headers['Content-Type'] = 'application/json';
                options.body = JSON.stringify(body);
            }
        }

        const response = await fetch(url, options);

        if (!response.ok) {
            throw new Error(`HTTP Error ${response.status}`);
        }

        const json = await response.json();

        // Standardized Reponse Handling
        // Expected format: { status: 0|1, data: T, error?: string }
        if (json.status === 1) {
            return json.data as T;
        } else {
            // Status 0 or missing means error
            throw new Error(json.error || "Unknown API Error");
        }
    }

    async get<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
        return this.request<T>('GET', endpoint, undefined, headers);
    }

    async post<T>(endpoint: string, body: RequestBody, headers?: Record<string, string>): Promise<T> {
        return this.request<T>('POST', endpoint, body, headers);
    }

    async put<T>(endpoint: string, body: RequestBody, headers?: Record<string, string>): Promise<T> {
        return this.request<T>('PUT', endpoint, body, headers);
    }

    async delete<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
        return this.request<T>('DELETE', endpoint, undefined, headers);
    }

    async patch<T>(endpoint: string, body: RequestBody, headers?: Record<string, string>): Promise<T> {
        return this.request<T>('PATCH', endpoint, body, headers);
    }

}

export const httpClient = new ApiClient();

// Specific API Calls
export const api = {
    voices: {
        list: () => httpClient.get<{ voices: Voice[], count: number }>('/api/voices'),
        create: (formData: FormData) => httpClient.post<{ voice_id: string; name: string; message: string }>('/api/voices/register', formData),
        delete: (id: string) => httpClient.delete<{ message: string }>(`/api/voices/${id}`),
    },
    emotions: {
        list: () => httpClient.get<{ emotions: Record<string, any>; count: number }>('/api/emotions'),
    },
    tts: {
        synthesize: (formData: FormData) => httpClient.post<SynthesisResponse>('/api/tts', formData),
    }
};
