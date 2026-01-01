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
            let errorMessage = `HTTP Error ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                // response was not JSON
            }
            throw new Error(errorMessage);
        }

        return response.json();
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
        list: () => httpClient.get<{ success: boolean; voices: Voice[] }>('/api/voices'),
        create: (formData: FormData) => httpClient.post<{ success: boolean; voice_id?: string; detail?: string }>('/api/voices/register', formData),
        delete: (id: string) => httpClient.delete<{ success: boolean }>(`/api/voices/${id}`),
    },
    emotions: {
        list: () => httpClient.get<{ success: boolean; emotions: string[] }>('/api/emotions'),
    },
    tts: {
        synthesize: (formData: FormData) => httpClient.post<SynthesisResponse>('/api/tts', formData),
    }
};
