"use client";

import { useEffect, useState } from 'react';
import { httpClient } from '@/lib/api';

export function StatusBanner() {
    const [status, setStatus] = useState<'connected' | 'connecting' | 'error'>('connecting');
    const [retryCount, setRetryCount] = useState(0);

    useEffect(() => {
        let mounted = true;
        let interval: NodeJS.Timeout;

        const checkHealth = async () => {
            try {
                await httpClient.get('/api/status');
                if (mounted) {
                    if (status !== 'connected') {
                        setStatus('connected');
                        // connection restored
                    }
                }
            } catch (error) {
                if (mounted) {
                    setStatus('error');
                    setRetryCount(prev => prev + 1);
                }
            }
        };

        // Initial check
        checkHealth();

        // Poll every 5 seconds
        interval = setInterval(checkHealth, 5000);

        return () => {
            mounted = false;
            clearInterval(interval);
        };
    }, []);

    if (status === 'connected') return null;

    return (
        <div className={`
      fixed bottom-0 left-0 right-0 p-2 text-center text-xs font-mono transition-colors duration-300 z-50
      ${status === 'connecting' ? 'bg-yellow-500/90 text-black' : 'bg-red-500/90 text-white'}
    `}>
            {status === 'connecting' && "Connecting to VoxLabs Engine..."}
            {status === 'error' && `Cannot connect to Voice Engine. Retrying (${retryCount})...`}
        </div>
    );
}
