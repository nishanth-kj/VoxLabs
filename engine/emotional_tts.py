"""
Emotional TTS Engine Module
Provides emotional control for text-to-speech synthesis
"""

from gtts import gTTS
from pydub import AudioSegment
import numpy as np
import io
from typing import Optional


class EmotionalTTSEngine:
    """
    Emotional TTS Engine with advanced voice modulation
    Supports speed, pitch, energy, and emotional tone control
    """
    
    def __init__(self):
        self.emotions = {
            'neutral': {'speed': 1.0, 'pitch': 1.0, 'energy': 1.0},
            'happy': {'speed': 1.2, 'pitch': 1.1, 'energy': 1.2},
            'sad': {'speed': 0.8, 'pitch': 0.9, 'energy': 0.7},
            'angry': {'speed': 1.3, 'pitch': 1.2, 'energy': 1.5},
            'calm': {'speed': 0.9, 'pitch': 0.95, 'energy': 0.8},
            'excited': {'speed': 1.4, 'pitch': 1.15, 'energy': 1.4},
            'fearful': {'speed': 1.1, 'pitch': 1.3, 'energy': 0.9},
            'confident': {'speed': 1.0, 'pitch': 0.95, 'energy': 1.1}
        }
    
    def synthesize(
        self,
        text: str,
        language: str = 'en',
        emotion: str = 'neutral',
        speed: Optional[float] = None,
        pitch: Optional[float] = None,
        energy: Optional[float] = None
    ) -> bytes:
        """Synthesize speech with emotional control"""
        # Get emotion parameters
        emotion_params = self.emotions.get(emotion, self.emotions['neutral'])
        
        # Override with custom parameters
        final_speed = speed if speed is not None else emotion_params['speed']
        final_pitch = pitch if pitch is not None else emotion_params['pitch']
        final_energy = energy if energy is not None else emotion_params['energy']
        
        # Generate base TTS
        tts = gTTS(text=text, lang=language, slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        
        # Load and process audio
        audio = AudioSegment.from_mp3(audio_fp)
        audio = self._apply_modulation(audio, final_speed, final_pitch, final_energy)
        
        # Export
        output = io.BytesIO()
        audio.export(output, format="mp3")
        return output.getvalue()
    
    def _apply_modulation(
        self,
        audio: AudioSegment,
        speed: float,
        pitch: float,
        energy: float
    ) -> AudioSegment:
        """Apply speed, pitch, and energy modulation"""
        # Apply speed
        if speed != 1.0:
            audio = audio.speedup(playback_speed=speed)
        
        # Apply pitch
        if pitch != 1.0:
            new_sample_rate = int(audio.frame_rate * pitch)
            audio = audio._spawn(
                audio.raw_data,
                overrides={"frame_rate": new_sample_rate}
            )
            audio = audio.set_frame_rate(44100)
        
        # Apply energy (volume)
        if energy != 1.0:
            change_in_dB = 20 * np.log10(energy)
            audio = audio + change_in_dB
        
        return audio
    
    def get_emotions(self) -> list:
        """Get list of available emotions"""
        return list(self.emotions.keys())
