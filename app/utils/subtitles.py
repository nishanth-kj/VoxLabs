"""SRT and WebVTT subtitle parsing, extraction, and formatting with millisecond precision."""

import re

# Match standard SRT timestamp: 00:01:23,456 --> 00:01:26,789
_SRT_TIME = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})"
)
# Match VTT timestamp with optional hours: 01:23.456 or 00:01:23.456
_VTT_TIME = re.compile(
    r"(?:(\d{1,2}):)?(\d{2}):(\d{2})[.](\d{3})\s*-->\s*(?:(\d{1,2}):)?(\d{2}):(\d{2})[.](\d{3})"
)
# Match speaker tags: <v Speaker Name>Text or [Speaker Name]: Text or Speaker Name: Text
_VTT_VOICE_TAG = re.compile(r"<v\s+([^>]+)>(.*)", re.DOTALL)
_BRACKET_SPEAKER = re.compile(r"^\[([A-Za-z0-9_\s\-\.]{1,40})\]\s*:\s*(.*)", re.DOTALL)
_COLON_SPEAKER = re.compile(r"^([A-Z][A-Za-z0-9_\s\-\.]{1,30})\s*:\s*(.*)", re.DOTALL)


def ms_to_timestamp(ms: int, separator: str = ",") -> str:
    """Format milliseconds into HH:MM:SS,mmm or HH:MM:SS.mmm."""
    ms = max(0, int(ms))
    total_seconds, milliseconds = divmod(ms, 1000)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{milliseconds:03d}"


def timestamp_to_ms(hours: str | int | None, minutes: str | int, seconds: str | int, millis: str | int) -> int:
    """Convert time components to milliseconds."""
    h = int(hours or 0)
    m = int(minutes)
    s = int(seconds)
    ms = int(millis)
    return (h * 3600 + m * 60 + s) * 1000 + ms


def extract_speaker_and_text(raw_text: str, default_speaker: str = "Narrator") -> tuple[str, str]:
    """Extract speaker name and cleaned text from a subtitle block."""
    text = raw_text.strip()
    # Check WebVTT <v Speaker> tag
    if m := _VTT_VOICE_TAG.match(text):
        speaker = m.group(1).strip()
        cleaned = re.sub(r"</v>", "", m.group(2)).strip()
        return speaker or default_speaker, cleaned
    # Check [Speaker]: Text
    if m := _BRACKET_SPEAKER.match(text):
        speaker = m.group(1).strip()
        cleaned = m.group(2).strip()
        return speaker or default_speaker, cleaned
    # Check Speaker: Text
    if m := _COLON_SPEAKER.match(text):
        speaker = m.group(1).strip()
        cleaned = m.group(2).strip()
        return speaker or default_speaker, cleaned
    return default_speaker, text


def parse_srt(content: str) -> list[dict]:
    """Parse SRT subtitle text into list of dicts:
    [{position, start_ms, end_ms, speaker, text}]
    """
    blocks = re.split(r"\r?\n\s*\r?\n", content.strip())
    segments = []
    position = 0
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        # Find the timestamp line
        time_index = -1
        match = None
        for i, line in enumerate(lines):
            match = _SRT_TIME.search(line)
            if match:
                time_index = i
                break
        if not match or time_index == -1:
            continue

        start_ms = timestamp_to_ms(match.group(1), match.group(2), match.group(3), match.group(4))
        end_ms = timestamp_to_ms(match.group(5), match.group(6), match.group(7), match.group(8))
        raw_text = " ".join(lines[time_index + 1:])
        raw_text = re.sub(r"<[^>]+>", "", raw_text)  # Strip inline HTML styling
        speaker, text = extract_speaker_and_text(raw_text)
        if not text:
            continue

        segments.append({
            "position": position,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "speaker": speaker,
            "text": text,
        })
        position += 1
    return segments


def parse_vtt(content: str) -> list[dict]:
    """Parse WebVTT subtitle text into list of dicts:
    [{position, start_ms, end_ms, speaker, text}]
    """
    lines = content.strip().splitlines()
    # Strip WEBVTT header
    if lines and lines[0].strip().startswith("WEBVTT"):
        lines = lines[1:]
    content_without_header = "\n".join(lines)
    blocks = re.split(r"\r?\n\s*\r?\n", content_without_header.strip())
    segments = []
    position = 0
    for block in blocks:
        block_lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not block_lines:
            continue
        # Ignore NOTE, STYLE, REGION blocks
        if block_lines[0].startswith(("NOTE", "STYLE", "REGION")):
            continue

        time_index = -1
        match = None
        for i, line in enumerate(block_lines):
            match = _VTT_TIME.search(line)
            if match:
                time_index = i
                break
        if not match or time_index == -1:
            continue

        start_ms = timestamp_to_ms(match.group(1), match.group(2), match.group(3), match.group(4))
        end_ms = timestamp_to_ms(match.group(5), match.group(6), match.group(7), match.group(8))
        raw_text = " ".join(block_lines[time_index + 1:])
        speaker, text = extract_speaker_and_text(raw_text)
        text = re.sub(r"<[^>]+>", "", text)  # Strip any remaining tags
        if not text:
            continue

        segments.append({
            "position": position,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "speaker": speaker,
            "text": text,
        })
        position += 1
    return segments


def parse_subtitles(content: str, format: str = "srt") -> list[dict]:
    """Parse either SRT or WebVTT subtitles."""
    fmt = format.lower().strip().lstrip(".")
    if fmt == "vtt" or "WEBVTT" in content[:60]:
        return parse_vtt(content)
    return parse_srt(content)


def to_srt(segments: list[dict], text_key: str = "text") -> str:
    """Format segments into SRT string."""
    out = []
    for idx, seg in enumerate(segments, 1):
        start = ms_to_timestamp(seg.get("start_ms", 0), separator=",")
        end = ms_to_timestamp(seg.get("end_ms", 0), separator=",")
        speaker = seg.get("speaker")
        text = seg.get(text_key, "")
        line_content = f"[{speaker}]: {text}" if speaker and speaker != "Narrator" else text
        out.append(f"{idx}\n{start} --> {end}\n{line_content}\n")
    return "\n".join(out)


def to_vtt(segments: list[dict], text_key: str = "text") -> str:
    """Format segments into WebVTT string."""
    out = ["WEBVTT\n"]
    for seg in segments:
        start = ms_to_timestamp(seg.get("start_ms", 0), separator=".")
        end = ms_to_timestamp(seg.get("end_ms", 0), separator=".")
        speaker = seg.get("speaker")
        text = seg.get(text_key, "")
        line_content = f"<v {speaker}>{text}" if speaker and speaker != "Narrator" else text
        out.append(f"{start} --> {end}\n{line_content}\n")
    return "\n".join(out)

