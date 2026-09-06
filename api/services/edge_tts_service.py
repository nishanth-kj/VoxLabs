import edge_tts
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
import tempfile
import os
from utils.logger import logger

class EdgeTTSService:
    """
    Service for interacting with Microsoft Edge TTS.
    Provides methods to list voices and generate speech.
    """

    def __init__(self):
        self.audio_dir = Path("static/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    async def get_voices(self) -> List[Dict]:
        """
        List all available Edge TTS voices.
        """
        try:
            logger.info("Fetching Edge TTS voice list...")
            voices = await edge_tts.list_voices()
            logger.debug(f"Retrieved {len(voices)} Edge voices")
            return [
                {
                    "ShortName": voice["ShortName"],
                    "FriendlyName": voice["FriendlyName"],
                    "Gender": voice["Gender"],
                    "Locale": voice["Locale"],
                }
                for voice in voices
            ]
        except Exception as e:
            logger.error(f"Error fetching Edge TTS voices: {str(e)}", exc_info=True)
            raise

    async def generate_speech(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> bytes:
        """
        Generate speech from text using the specified voice and parameters.
        """
        try:
            logger.info(f"Edge synthesis started: voice={voice}, rate={rate}")
            logger.debug(f"Input text: {text[:50]}...")
            
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
            
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            logger.info(f"Edge synthesis completed ({len(audio_data)} bytes)")
            return audio_data
        except Exception as e:
            logger.error(f"Edge synthesis error: {str(e)}", exc_info=True)
            raise

    async def generate_and_save(
        self,
        text: str,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%"
    ) -> Dict:
        """Generate speech, save it to the audio directory, and return a response-ready dict."""
        audio_data = await self.generate_speech(text=text, voice=voice, rate=rate, pitch=pitch, volume=volume)

        filename = f"edge_{hash(text)}_{voice.split('-')[-1]}.mp3"
        filepath = self.audio_dir / filename
        with open(filepath, "wb") as f:
            f.write(audio_data)
        logger.debug(f"Edge audio file saved: {filepath}")

        return {
            "audio_url": f"/static/audio/{filename}",
            "engine": "edge",
            "message": "Edge speech generated successfully"
        }
