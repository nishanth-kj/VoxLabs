import edge_tts
import asyncio
from typing import List, Dict, Optional
import tempfile
import os
from utils.logger import logger

class EdgeTTSService:
    """
    Service for interacting with Microsoft Edge TTS.
    Provides methods to list voices and generate speech.
    """

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
