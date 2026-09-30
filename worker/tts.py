"""Offline, registration-free text-to-speech narration using eSpeak NG."""
import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
AUDIO_DIR = DATA_DIR / "audio"
TARGET_SCENE_SECONDS = 16.5
TTS_VOICE = os.getenv("TTS_VOICE", "en-us")
TTS_RATE = os.getenv("TTS_RATE", "155")
TTS_PITCH = os.getenv("TTS_PITCH", "50")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def _speak(text: str, output_wav: Path) -> None:
    binary = shutil.which("espeak-ng") or shutil.which("espeak")
    if not binary:
        raise RuntimeError("espeak-ng is not installed")
    result = subprocess.run(
        [binary, "-v", TTS_VOICE, "-s", str(TTS_RATE), "-p", str(TTS_PITCH),
         "-w", str(output_wav), text],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1500:] or "eSpeak NG failed")


def _convert_to_wav(source: Path, target: Path) -> None:
    result = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(source),
         "-ar", "22050", "-ac", "1", "-c:a", "pcm_s16le", str(target)],
        capture_output=True, timeout=60, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1500:] or "Audio conversion failed")


async def _generate_scene_audio(text: str, output_wav: Path) -> None:
    _speak(text, output_wav)
    normalized = output_wav.with_suffix(".normalized.wav")
    _convert_to_wav(output_wav, normalized)
    normalized.replace(output_wav)


async def generate_narration_from_story(story: dict, job_id: str) -> dict:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Generating offline narration for job %s", job_id)

    scene_files = []
    total_duration = 0.0
    subtitle_entries = []
    current_time = 0.0

    for i, scene in enumerate(story.get("scenes", []), 1):
        narration_text = (scene.get("narration") or "").strip() or "Let's see what happens next."
        scene_audio_file = AUDIO_DIR / f"{job_id}_scene_{i:03d}.wav"
        target_duration = TARGET_SCENE_SECONDS
        await _generate_scene_audio(narration_text, scene_audio_file)

        spoken_duration = _get_audio_duration(str(scene_audio_file))
        if spoken_duration <= 0:
            raise RuntimeError(f"Scene {i} produced invalid narration audio")

        if spoken_duration > target_duration or spoken_duration < target_duration * 0.7:
            tempo = spoken_duration / target_duration
            factors = []
            while tempo > 2.0:
                factors.append("2.0")
                tempo /= 2.0
            while tempo < 0.5:
                factors.append("0.5")
                tempo /= 0.5
            factors.append(f"{tempo:.6f}")
            normalized = AUDIO_DIR / f"{job_id}_scene_{i:03d}_normalized.wav"
            result = subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(scene_audio_file),
                 "-af", ",".join(f"atempo={x}" for x in factors) + f",apad,atrim=duration={target_duration:.3f}",
                 "-ar", "22050", "-ac", "1", "-c:a", "pcm_s16le", str(normalized)],
                capture_output=True, timeout=60, text=True,
            )
            if result.returncode:
                raise RuntimeError(result.stderr[-1200:] or "Narration normalization failed")
            normalized.replace(scene_audio_file)
        else:
            result = subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(scene_audio_file),
                 "-af", f"apad,atrim=duration={target_duration:.3f}",
                 "-ar", "22050", "-ac", "1", "-c:a", "pcm_s16le", str(scene_audio_file.with_suffix(".pad.wav"))],
                capture_output=True, timeout=60, text=True,
            )
            if result.returncode:
                raise RuntimeError(result.stderr[-1200:] or "Narration padding failed")
            Path(scene_audio_file.with_suffix(".pad.wav")).replace(scene_audio_file)

        scene_files.append({"path": str(scene_audio_file), "duration": target_duration,
                            "scene_num": i, "text": narration_text})
        subtitle_entries.append({
            "index": i,
            "start": _format_srt_time(current_time),
            "end": _format_srt_time(current_time + min(spoken_duration, target_duration)),
            "text": narration_text[:220],
            "scene_title": scene.get("title", f"Scene {i}"),
        })
        current_time += target_duration
        total_duration += target_duration

    narration_file = AUDIO_DIR / f"{job_id}_narration.wav"
    _combine_audio_files(scene_files, str(narration_file))
    subtitles_file = _generate_subtitles(job_id, subtitle_entries)
    logger.info("Offline narration complete: %.2fs", total_duration)
    return {
        "narration_file": str(narration_file),
        "scene_narrations": scene_files,
        "subtitles_file": str(subtitles_file),
        "total_duration": total_duration,
    }


def _get_audio_duration(audio_file: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_file],
        capture_output=True, timeout=10, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return float(result.stdout.strip())
    return 0.0


def _combine_audio_files(scene_files: list, output_file: str) -> None:
    concat_file = Path(output_file).parent / f"{Path(output_file).stem}_concat.txt"
    try:
        with open(concat_file, "w", encoding="utf-8") as f:
            for scene in scene_files:
                f.write(f"file '{Path(scene['path']).resolve()}'\n")
        result = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", str(concat_file), "-c", "copy", output_file],
            capture_output=True, timeout=180, text=True,
        )
        if result.returncode:
            raise RuntimeError(result.stderr[-1500:] or "Audio combine failed")
    finally:
        concat_file.unlink(missing_ok=True)


def _generate_subtitles(job_id: str, subtitle_entries: list) -> str:
    srt_file = AUDIO_DIR / f"{job_id}_subtitles.srt"
    with open(srt_file, "w", encoding="utf-8") as f:
        for entry in subtitle_entries:
            f.write(f"{entry['index']}\n{entry['start']} --> {entry['end']}\n"
                    f"{entry['scene_title']}\n{entry['text']}\n\n")
    return str(srt_file)


def _format_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
