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

        const maxRetries = 3;
        let attempt = 0;
        let lastError = null;

        while (attempt < maxRetries) {
            try {
                const response = await fetch(url, options);

                if (!response.ok) {
                    throw new Error(`HTTP Error ${response.status}`);
                }

                const json = await response.json();

                // Standardized Response Handling
                if (json.status === 1) {
                    return json.data as T;
                } else {
                    const errorMessage = json.error?.message || (typeof json.error === 'string' ? json.error : "Unknown API Error");
                    throw new Error(errorMessage);
                }
            } catch (error) {
                lastError = error;
                // Only retry on network errors (fetch throws) or 5xx errors
                // If it's an API error (status 0), don't retry
                if (error instanceof Error && error.message.includes("HTTP Error 5")) {
                    attempt++;
                    await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                } else if (error instanceof TypeError) { // Network error
                    attempt++;
                    await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                } else {
                    throw error;
                }
            }
        }
        throw lastError;
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
        design: (formData: FormData) => httpClient.post<{ voice_id: string; message: string }>('/api/voices/design', formData),
        delete: (id: string) => httpClient.delete<{ message: string }>(`/api/voices/${id}`),
        sourceUrl: (id: string) => `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/voices/${id}/source`,
    },
    emotions: {
        list: () => httpClient.get<{ emotions: Record<string, any>; count: number }>('/api/emotions'),
    },
    tts: {
        synthesize: (formData: FormData) => httpClient.post<SynthesisResponse>('/api/tts', formData),
        listEdgeVoices: () => httpClient.get<any[]>('/api/tts/edge/voices'),
        synthesizeEdge: (data: any) => httpClient.post<SynthesisResponse>('/api/tts/edge/generate', data),
    }
};
