"""What the Library's Files page lists: every kind of audio VoxLabs keeps, in display order."""

from app.constants.audio_source import AudioSource

LIBRARY_KINDS = {
    AudioSource.GENERATED: "Generated speech",
    AudioSource.IMPORTED: "Imported",
    AudioSource.PROCESSED: "Processed",
    AudioSource.RENDERED: "Edited and rendered",
    "export": "Exported",
    AudioSource.SAMPLE: "Voice sample",
}
