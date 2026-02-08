"""
Emotional TTS Engine Module
Provides emotional control for text-to-speech synthesis
"""

from gtts import gTTS
from pydub import AudioSegment
import numpy as np
import io
import librosa
import soundfile as sf
from typing import Optional
from utils.logger import logger


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
        try:
            logger.info(f"Emotional synthesis started: lang={language}, emotion={emotion}")
            logger.debug(f"Input text: {text[:50]}...")
            
            # Get emotion parameters
            emotion_params = self.emotions.get(emotion, self.emotions['neutral'])
            
            # Override with custom parameters
            final_speed = speed if speed is not None else emotion_params['speed']
            final_pitch = pitch if pitch is not None else emotion_params['pitch']
            final_energy = energy if energy is not None else emotion_params['energy']
            
            logger.debug(f"Applied params: speed={final_speed}, pitch={final_pitch}, energy={final_energy}")

            # Generate base TTS using gTTS
            tts = gTTS(text=text, lang=language, slow=False)
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            
            # Load into librosa
            y, sr = librosa.load(audio_fp, sr=None)
            
            # Apply modulations
            # 1. Pitch Shift
            if final_pitch != 1.0 and final_pitch > 0:
                n_steps = 12 * np.log2(final_pitch)
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)
                logger.debug(f"Applied pitch shift: {n_steps} steps")

            # 2. Speed Shift (Time Stretch)
            if final_speed != 1.0 and final_speed > 0:
                y = librosa.effects.time_stretch(y, rate=final_speed)
                logger.debug(f"Applied time stretch: {final_speed}x")

            # 3. Energy (Volume Gain)
            if final_energy != 1.0 and final_energy > 0:
                y = y * final_energy
                # Clip to avoid distortion
                max_val = np.abs(y).max()
                if max_val > 1.0:
                    y = y / max_val
                logger.debug(f"Applied energy scaling: {final_energy}x")
            
            # Convert back to MP3
            wav_buffer = io.BytesIO()
            sf.write(wav_buffer, y, sr, format='WAV')
            wav_buffer.seek(0)
            
            audio_segment = AudioSegment.from_wav(wav_buffer)
            
            output = io.BytesIO()
            audio_segment.export(output, format="mp3")
            
            logger.info("Emotional synthesis completed successfully")
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Emotional synthesis error: {str(e)}", exc_info=True)
            raise e

    
    def get_emotions(self) -> dict:
        """Get dict of available emotions with their default parameters"""
        return self.emotions
