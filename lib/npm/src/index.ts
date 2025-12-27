export { VoiceSynthesizer } from './synthesizer';
export { VoiceCloner } from './cloner';
export { AudioProcessor } from './processor';
export { VoiceStorage } from './storage';

export interface VoxLabsConfig {
    apiUrl?: string;
    offline?: boolean;
    watermark?: boolean;
}
