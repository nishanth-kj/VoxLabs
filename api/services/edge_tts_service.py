import edge_tts
import asyncio
from typing import List, Dict, Optional
import tempfile
import os

class EdgeTTSService:
    """
    Service for interacting with Microsoft Edge TTS.
    Provides methods to list voices and generate speech.
    """

    async def get_voices(self) -> List[Dict]:
        """
        List all available Edge TTS voices.
        Returns a list of dictionaries containing voice details.
        """
        voices = await edge_tts.list_voices()
        return [
            {
                "ShortName": voice["ShortName"],
                "FriendlyName": voice["FriendlyName"],
                "Gender": voice["Gender"],
                "Locale": voice["Locale"],
            }
            for voice in voices
        ]

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
        
        Args:
            text: Works to be spoken.
            voice: The ShortName of the voice to use.
            rate: Speed of speech (e.g., "+10%", "-10%").
            pitch: Pitch of speech (e.g., "+10Hz", "-10Hz").
            volume: Volume of speech (e.g., "+10%", "-10%").
            
        Returns:
            Audio bytes (MP3 format).
        """
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
        
        # Create a temporary file to store the audio
        # edge-tts async API saves to file or yields bytes. 
        # For simplicity in this wrapper, we can collect bytes.
        
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
                
        return audio_data
