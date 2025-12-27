"""Voice storage module"""

class VoiceStorage:
    """Voice data storage"""
    
    def save(self, voice_id: str, data: bytes):
        """Save voice data"""
        pass
    
    def load(self, voice_id: str) -> bytes:
        """Load voice data"""
        pass
