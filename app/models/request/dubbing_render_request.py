from pydantic import BaseModel


class DubbingRenderRequest(BaseModel):
    """Render synchronized audio and remux output video."""

    dubbing_projects_id: int
    background_audio_mode: str = "duck"  # "duck" | "replace" | "mute"
    ducking_volume: float = 0.25  # ~ -12 dB
    video_quality: str = "copy"  # "copy" (lossless fast remux) | "reencode"
    audio_bitrate: str = "192k"
    output_path: str | None = None

