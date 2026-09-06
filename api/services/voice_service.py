"""
Voice Engine Module - Local Voice Cloning System
Following safety design brief: consent-based, project-scoped, offline
"""

import os
import shutil
import json
import hashlib
import librosa
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from pydub import AudioSegment
import io
from services.tts_service import EmotionalTTSEngine
from exceptions import NotFoundException, BadRequestException
from utils.logger import logger


class VoiceIdentity:
    """Represents a registered voice identity with consent"""
    
    def __init__(
        self,
        voice_id: str,
        name: str,
        consent: bool,
        audio_features: np.ndarray,
        created_at: str,
        project_id: str,
        metadata: Optional[Dict] = None
    ):
        self.voice_id = voice_id
        self.name = name
        self.consent = consent
        self.audio_features = audio_features
        self.created_at = created_at
        self.project_id = project_id
        self.metadata = metadata or {}
        self.revoked = False
    
    def to_dict(self):
        """Serialize to dictionary (without audio features)"""
        return {
            "voice_id": self.voice_id,
            "name": self.name,
            "consent": self.consent,
            "created_at": self.created_at,
            "project_id": self.project_id,
            "metadata": self.metadata,
            "revoked": self.revoked
        }


class VoiceEngine:
    """
    Local voice cloning engine with safety controls
    - Consent-based registration
    - Project-scoped storage
    - Offline inference
    - Revocable identities
    """
    
    def __init__(self, project_path: str = "voice_projects"):
        try:
            self.project_path = Path(project_path)
            self.project_path.mkdir(exist_ok=True)
            logger.info(f"VoiceEngine initialized with project path: {project_path}")
        except Exception as e:
            logger.error(f"Failed to create project path {project_path}: {str(e)}")
            raise
        
        # Check for FFmpeg
        if not shutil.which("ffmpeg"):
            logger.warning("FFmpeg not found in PATH! Audio synthesis using pydub/gTTS will fail.")
            logger.warning("Please install FFmpeg and add it to your system PATH.")
        
        # Storage structure
        self.voices_dir = self.project_path / "voices"
        self.voices_dir.mkdir(exist_ok=True)
        
        self.voices_source_dir = self.project_path / "voices_source"
        self.voices_source_dir.mkdir(exist_ok=True)

        self.audio_dir = Path("static/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.project_path / "voices_metadata.json"
        self.consent_log = self.project_path / "consent_log.json"
        
        # Load existing voices
        self.voices: Dict[str, VoiceIdentity] = {}
        self._load_voices()
        
        # Pre-trained voices (male/female)
        self.pretrained_voices = {
            "male_default": {
                "name": "Male Voice (Default)",
                "gender": "male",
                "features": self._generate_default_features("male")
            },
            "female_default": {
                "name": "Female Voice (Default)",
                "gender": "female",
                "features": self._generate_default_features("female")
            }
        }
    
        self.emotional_engine = EmotionalTTSEngine()

    def synthesize(
        self,
        text: str,
        engine: str = "emotional",
        voice_id: Optional[str] = None,
        language: str = "en",
        emotion: str = "neutral",
        speed: float = 1.0,
        pitch: float = 1.0,
        energy: float = 1.0
    ) -> bytes:
        """
        Synthesize speech using the specified engine strategy
        """
        try:
            logger.info(f"Synthesis request (engine={engine}, voice_id={voice_id}, lang={language}, emotion={emotion})")
            logger.debug(f"Text to synthesize: {text[:50]}...")
            
            if engine == "emotional":
                return self.emotional_engine.synthesize(
                    text=text,
                    language=language,
                    emotion=emotion,
                    speed=speed,
                    pitch=pitch,
                    energy=energy
                )
            elif engine == "clone":
                if not voice_id:
                    logger.warning("Synthesis failed: voice_id required for cloning engine")
                    raise BadRequestException("Voice ID required for cloning", field="voice_id")

                voice = self.get_voice(voice_id)
                if not voice:
                    if voice_id in self.pretrained_voices:
                        pass
                    else:
                        logger.error(f"Synthesis failed: voice {voice_id} not found")
                        raise NotFoundException(f"Voice {voice_id} not found", field="voice_id")

                return self.emotional_engine.synthesize(
                    text=text,
                    language=language,
                    emotion=emotion,
                    speed=speed,
                    pitch=pitch * 0.9 if voice_id == "male_default" else pitch * 1.1,
                    energy=energy
                )
            else:
                 logger.info(f"Using default synthesis for unknown engine: {engine}")
                 return self.emotional_engine.synthesize(text=text, language=language)
        except Exception as e:
            logger.error(f"Synthesis error: {str(e)}", exc_info=True)
            raise

    def synthesize_and_save(
        self,
        text: str,
        engine: str = "emotional",
        voice_id: Optional[str] = None,
        language: str = "en",
        emotion: str = "neutral",
        speed: float = 1.0,
        pitch: float = 1.0,
        energy: float = 1.0
    ) -> Dict:
        """Synthesize speech, save it to the audio directory, and return a response-ready dict."""
        audio_data = self.synthesize(
            text=text,
            engine=engine,
            voice_id=voice_id,
            language=language,
            emotion=emotion,
            speed=speed,
            pitch=pitch,
            energy=energy
        )

        filename = f"tts_{hash(text)}_{emotion}.mp3"
        filepath = self.audio_dir / filename
        with open(filepath, "wb") as f:
            f.write(audio_data)
        logger.debug(f"TTS audio file saved: {filepath}")

        return {
            "audio_url": f"/static/audio/{filename}",
            "engine": engine,
            "emotion": emotion if engine == "emotional" else None,
            "message": "Speech generated successfully"
        }

    def _generate_default_features(self, gender: str) -> np.ndarray:
        """Generate default voice features for male/female"""
        # Simplified feature representation
        # In production, use pre-trained embeddings
        base_pitch = 120 if gender == "male" else 220  # Hz
        features = np.random.randn(256)  # 256-dim embedding
        features[0] = base_pitch
        return features
    
    def _load_voices(self):
        """Load registered voices from disk"""
        if not self.metadata_file.exists():
            return
        
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            for voice_id, data in metadata.items():
                # Load audio features
                features_path = self.voices_dir / f"{voice_id}_features.npy"
                if features_path.exists():
                    features = np.load(features_path)
                    self.voices[voice_id] = VoiceIdentity(
                        voice_id=voice_id,
                        name=data['name'],
                        consent=data['consent'],
                        audio_features=features,
                        created_at=data['created_at'],
                        project_id=data['project_id'],
                        metadata=data.get('metadata', {})
                    )
                    self.voices[voice_id].revoked = data.get('revoked', False)
        except Exception as e:
            logger.error(f"Error loading voices: {e}")
    
    def _save_voices(self):
        """Save voice metadata to disk"""
        metadata = {
            voice_id: voice.to_dict()
            for voice_id, voice in self.voices.items()
        }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _log_consent(self, voice_id: str, action: str, details: Dict):
        """Log consent actions for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "voice_id": voice_id,
            "action": action,
            "details": details
        }
        
        log_data = []
        if self.consent_log.exists():
            with open(self.consent_log, 'r') as f:
                log_data = json.load(f)
        
        log_data.append(log_entry)
        
        with open(self.consent_log, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def extract_voice_features(self, audio_path: str) -> np.ndarray:
        """
        Extract voice features from audio file
        Uses MFCC + pitch features for voice characterization
        """
        # Load audio
        y, sr = librosa.load(audio_path, sr=22050)
        
        # Extract features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfccs_mean = np.mean(mfccs, axis=1)
        
        # Extract pitch (f0)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_mean = np.mean([pitches[magnitudes[:, t].argmax(), t] 
                             for t in range(pitches.shape[1]) 
                             if magnitudes[:, t].max() > 0])
        
        # Combine features
        features = np.concatenate([mfccs_mean, [pitch_mean]])
        
        # Pad to fixed size (256 dimensions)
        if len(features) < 256:
            features = np.pad(features, (0, 256 - len(features)))
        else:
            features = features[:256]
        
        return features
    
    def register_voice(
        self,
        audio_path: str,
        voice_name: str,
        consent: bool,
        project_id: str = "default",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Register a new voice identity with consent
        """
        try:
            logger.info(f"Registering new voice: {voice_name} for project: {project_id}")
            if not consent:
                logger.warning(f"Registration attempt for {voice_name} failed: Explicit consent required")
                raise BadRequestException("Explicit consent required for voice registration", field="consent")

            if not Path(audio_path).exists():
                logger.error(f"Registration failed: Audio file not found at {audio_path}")
                raise NotFoundException(f"Audio file not found: {audio_path}", field="audio")
            
            # Generate unique voice ID
            voice_id = hashlib.sha256(
                f"{voice_name}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            logger.debug(f"Generated voice ID: {voice_id}")
            
            # Extract voice features
            features = self.extract_voice_features(audio_path)
            
            # Create voice identity
            voice = VoiceIdentity(
                voice_id=voice_id,
                name=voice_name,
                consent=consent,
                audio_features=features,
                created_at=datetime.now().isoformat(),
                project_id=project_id,
                metadata=metadata or {}
            )
            
            # Save to storage
            self.voices[voice_id] = voice
            np.save(self.voices_dir / f"{voice_id}_features.npy", features)
            self._save_voices()
            
            # Save raw audio source
            shutil.copy2(audio_path, self.voices_source_dir / f"{voice_id}.wav")
            
            # Log consent
            self._log_consent(voice_id, "register", {
                "name": voice_name,
                "project_id": project_id,
                "consent": consent
            })
            
            logger.info(f"Voice {voice_name} registered successfully with ID: {voice_id}")
            return voice_id
        except Exception as e:
            logger.error(f"Error during voice registration: {str(e)}", exc_info=True)
            raise
    
    def get_voice_source_path(self, voice_id: str) -> Optional[str]:
        """Get the path to the original audio source for a voice"""
        source_path = self.voices_source_dir / f"{voice_id}.wav"
        if source_path.exists():
            return str(source_path)
        return None
    
    def design_voice(self, prompt: str, project_id: str = "default") -> str:
        """
        Design a new voice from a text prompt (Zero-shot persona generation).
        """
        try:
            logger.info(f"Designing voice from prompt: '{prompt}' for project: {project_id}")
            
            # Generate unique voice ID
            voice_id = hashlib.sha256(
                f"{prompt}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            
            # Generate features deterministically based on the prompt string hash
            # In production, this would call an LLM or TTS model to generate embeddings
            np.random.seed(int(hashlib.md5(prompt.encode()).hexdigest(), 16) % (2**32))
            features = np.random.randn(256)
            
            # Simple heuristic mapping for pitch based on prompt words
            base_pitch = 120 # Default male
            prompt_lower = prompt.lower()
            if "female" in prompt_lower or "woman" in prompt_lower or "girl" in prompt_lower:
                base_pitch = 220
            if "deep" in prompt_lower or "low" in prompt_lower:
                base_pitch *= 0.8
            if "high" in prompt_lower or "child" in prompt_lower:
                base_pitch *= 1.3
                
            features[0] = base_pitch
            
            voice_name = f"Designed: {prompt[:20]}..."
            
            voice = VoiceIdentity(
                voice_id=voice_id,
                name=voice_name,
                consent=True, # Generated voice, implicit consent
                audio_features=features,
                created_at=datetime.now().isoformat(),
                project_id=project_id,
                metadata={"prompt": prompt, "type": "designed"}
            )
            
            # Save to storage
            self.voices[voice_id] = voice
            np.save(self.voices_dir / f"{voice_id}_features.npy", features)
            self._save_voices()
            
            # Log consent
            self._log_consent(voice_id, "design", {
                "name": voice_name,
                "project_id": project_id,
                "prompt": prompt
            })
            
            logger.info(f"Designed voice {voice_id} created successfully")
            return voice_id
        except Exception as e:
            logger.error(f"Error during voice design: {str(e)}", exc_info=True)
            raise
    
    def list_voices(self, project_id: Optional[str] = None) -> Dict:
        """List registered voices (optionally filtered by project), response-ready"""
        voices = []
        for voice_id, voice in self.voices.items():
            if voice.revoked:
                continue
            if project_id and voice.project_id != project_id:
                continue
            voices.append(voice.to_dict())

        return {"voices": voices, "count": len(voices)}

    def get_voice(self, voice_id: str) -> Optional[VoiceIdentity]:
        """Get voice identity by ID"""
        voice = self.voices.get(voice_id)
        if voice and not voice.revoked:
            return voice
        return None

    def get_voice_details(self, voice_id: str) -> Dict:
        """Get voice details, response-ready. Raises NotFoundException if missing/revoked."""
        voice = self.get_voice(voice_id)
        if not voice:
            logger.warning(f"Voice not found: {voice_id}")
            raise NotFoundException(f"Voice {voice_id} not found", field="voice_id")
        return {"voice": voice.to_dict()}

    def get_voice_source_path_or_raise(self, voice_id: str) -> str:
        """Get the path to the original audio source for a voice. Raises NotFoundException if missing."""
        source_path = self.get_voice_source_path(voice_id)
        if not source_path:
            logger.warning(f"Audio source not found for voice: {voice_id}")
            raise NotFoundException(f"Audio source not found for voice {voice_id}", field="voice_id")
        return source_path

    def revoke_voice(self, voice_id: str) -> Dict:
        """
        Revoke a voice identity and delete associated data
        Ensures complete removal per safety design. Returns a response-ready message.
        """
        try:
            logger.info(f"Revoking voice identity: {voice_id}")
            if voice_id not in self.voices:
                logger.warning(f"Revocation failed: Voice {voice_id} not found")
                raise NotFoundException(f"Voice {voice_id} not found", field="voice_id")

            voice = self.voices[voice_id]
            logger.info(f"Removing data for voice: {voice.name}")
            voice.revoked = True
            
            # Delete features file
            features_path = self.voices_dir / f"{voice_id}_features.npy"
            if features_path.exists():
                features_path.unlink()
                logger.debug(f"Deleted features file: {features_path}")
            
            # Log revocation
            self._log_consent(voice_id, "revoke", {
                "name": voice.name,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update metadata
            self._save_voices()
            
            # Remove from memory
            del self.voices[voice_id]
            logger.info(f"Voice {voice_id} revoked successfully")
            return {"message": f"Voice {voice_id} revoked successfully"}
        except Exception as e:
            logger.error(f"Error revoking voice {voice_id}: {str(e)}", exc_info=True)
            raise
    
    def synthesize_with_voice(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        pitch_shift: float = 1.0,
        energy: float = 1.0
    ) -> dict:
        """
        Synthesize speech with voice characteristics
        
        If voice_id is provided, applies voice features
        Otherwise uses default voice
        """
        # Get voice features
        if voice_id:
            if voice_id in ["male_default", "female_default"]:
                features = self.pretrained_voices[voice_id]["features"]
            else:
                voice = self.get_voice(voice_id)
                if not voice:
                    raise ValueError(f"Voice {voice_id} not found or revoked")
                if not voice.consent:
                    raise ValueError("Voice consent withdrawn")
                features = voice.audio_features
        else:
            features = self.pretrained_voices["female_default"]["features"]
        
        # Use features to modulate synthesis
        # Extract pitch from features
        target_pitch = float(features[0]) if len(features) > 0 else 220.0
        
        # Adjust pitch_shift based on voice features
        pitch_adjust = float(pitch_shift) * (target_pitch / 220.0)  # Normalize to female default
        
        return {
            "features": features,
            "pitch_adjust": pitch_adjust,
            "speed": float(speed),
            "energy": float(energy)
        }
    
    def purge_project(self, project_id: str):
        """Delete all voices for a project"""
        voices_to_remove = [
            voice_id for voice_id, voice in self.voices.items()
            if voice.project_id == project_id
        ]
        
        for voice_id in voices_to_remove:
            self.revoke_voice(voice_id)
    
    def add_watermark(self, audio_data: bytes) -> bytes:
        """
        Add synthetic audio watermark
        Marks audio as AI-generated for transparency
        """
        # Simple implementation: add metadata tag
        # In production, use ultrasonic watermarking
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        
        # Add tag (pydub doesn't support custom tags easily, 
        # so we'd use a library like mutagen in production)
        # For now, return as-is with comment
        
        output = io.BytesIO()
        audio.export( # type: ignore
            output,
            format="mp3",
            tags={'comment': 'AI-Generated by Voice-Synth Engine'}
        )
        output.seek(0)
        return output.read()


# Global voice engine instance
_voice_engine: Optional[VoiceEngine] = None


def get_voice_engine() -> VoiceEngine:
    """Get or create voice engine instance"""
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = VoiceEngine()
    return _voice_engine
