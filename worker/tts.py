"""Neural text-to-speech narration with a reliable local fallback."""
import asyncio
import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
AUDIO_DIR = DATA_DIR / "audio"
TARGET_SCENE_SECONDS = 16.5
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-JennyNeural")
TTS_RATE = os.getenv("TTS_RATE", "-5%")
TTS_PITCH = os.getenv("TTS_PITCH", "+0Hz")
REQUIRE_NEURAL_TTS = os.getenv("REQUIRE_NEURAL_TTS", "false").lower() == "true"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)


async def _neural_tts(text: str, output_mp3: Path) -> None:
    """Generate natural neural speech using Microsoft Edge's neural TTS service."""
    import edge_tts

    communicate = edge_tts.Communicate(
        text=text,
        voice=TTS_VOICE,
        rate=TTS_RATE,
        pitch=TTS_PITCH,
    )
    await communicate.save(str(output_mp3))


def _espeak_fallback(text: str, output_wav: Path) -> None:
    """Local fallback if neural TTS is temporarily unavailable."""
    result = subprocess.run(
        ["espeak-ng", "-w", str(output_wav), "-s", "145", "-p", "52", "--", text[:700]],
        capture_output=True,
        timeout=45,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1000:] or "eSpeak failed")


def _convert_to_wav(source: Path, target: Path) -> None:
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(source),
            "-ar", "22050", "-ac", "1", "-c:a", "pcm_s16le", str(target),
        ],
        capture_output=True,
        timeout=60,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1500:] or "Audio conversion failed")


async def _generate_scene_audio(text: str, output_wav: Path) -> None:
    mp3 = output_wav.with_suffix(".mp3")
    try:
        await _neural_tts(text, mp3)
        _convert_to_wav(mp3, output_wav)
        mp3.unlink(missing_ok=True)
        logger.info("Neural TTS generated with %s", TTS_VOICE)
    except Exception as exc:
        mp3.unlink(missing_ok=True)
        if REQUIRE_NEURAL_TTS:
            raise RuntimeError(f"Neural TTS failed and REQUIRE_NEURAL_TTS is enabled: {exc}") from exc
        logger.warning("Neural TTS failed (%s); using local fallback", exc)
        _espeak_fallback(text, output_wav)


async def generate_narration_from_story(story: dict, job_id: str) -> dict:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Generating human-style narration for job %s", job_id)

    scene_files = []
    total_duration = 0.0
    subtitle_entries = []
    current_time = 0.0

    for i, scene in enumerate(story.get("scenes", []), 1):
        narration_text = (scene.get("narration") or "").strip() or "Let's see what happens next."
        scene_audio_file = AUDIO_DIR / f"{job_id}_scene_{i:03d}.wav"
        target_duration = TARGET_SCENE_SECONDS

        try:
            await _generate_scene_audio(narration_text, scene_audio_file)
            spoken_duration = _get_audio_duration(str(scene_audio_file))
            if spoken_duration <= 0:
                raise RuntimeError("Generated audio has no measurable duration")

            if abs(spoken_duration - target_duration) > 0.05:
                if spoken_duration < target_duration:
                    filter_expr = (
                        f"apad=pad_dur={target_duration - spoken_duration:.3f},"
                        f"atrim=duration={target_duration:.3f}"
                    )
                else:
                    tempo = spoken_duration / target_duration
                    factors = []
                    while tempo > 2.0:
                        factors.append("2.0")
                        tempo /= 2.0
                    while tempo < 0.5:
                        factors.append("0.5")
                        tempo /= 0.5
                    factors.append(f"{tempo:.6f}")
                    filter_expr = ",".join(f"atempo={factor}" for factor in factors)
                    filter_expr += f",atrim=duration={target_duration:.3f}"

                normalized = AUDIO_DIR / f"{job_id}_scene_{i:03d}_normalized.wav"
                result = subprocess.run(
                    [
                        "ffmpeg", "-y", "-v", "error", "-i", str(scene_audio_file),
                        "-af", filter_expr, "-ar", "22050", "-ac", "1",
                        "-c:a", "pcm_s16le", str(normalized),
                    ],
                    capture_output=True, timeout=60, text=True,
                )
                if result.returncode != 0:
                    raise RuntimeError(result.stderr[-1200:] or "Normalization failed")
                normalized.replace(scene_audio_file)

            scene_files.append({
                "path": str(scene_audio_file),
                "duration": target_duration,
                "scene_num": i,
                "text": narration_text,
            })
            subtitle_entries.append({
                "index": i,
                "start": _format_srt_time(current_time),
                "end": _format_srt_time(current_time + min(spoken_duration, target_duration)),
                "text": narration_text[:220],
                "scene_title": scene.get("title", f"Scene {i}"),
            })
            current_time += target_duration
            total_duration += target_duration
            logger.info("Scene %s: %.2fs spoken, %.2fs timeline", i, spoken_duration, target_duration)
        except Exception as exc:
            logger.error("Scene %s TTS failed: %s", i, exc)
            if REQUIRE_NEURAL_TTS:
                raise RuntimeError(
                    f"Production neural TTS failed for scene {i}: {exc}"
                ) from exc
            _create_silent_audio(str(scene_audio_file), target_duration)
            scene_files.append({
                "path": str(scene_audio_file),
                "duration": target_duration,
                "scene_num": i,
                "text": narration_text,
            })
            subtitle_entries.append({
                "index": i,
                "start": _format_srt_time(current_time),
                "end": _format_srt_time(current_time + target_duration),
                "text": narration_text[:220],
                "scene_title": scene.get("title", f"Scene {i}"),
            })
            current_time += target_duration
            total_duration += target_duration

    narration_file = AUDIO_DIR / f"{job_id}_narration.wav"
    _combine_audio_files(scene_files, str(narration_file))
    subtitles_file = _generate_subtitles(job_id, subtitle_entries)

    logger.info("Narration complete: %.2fs using %s", total_duration, TTS_VOICE)
    return {
        "narration_file": str(narration_file),
        "scene_narrations": scene_files,
        "subtitles_file": str(subtitles_file),
        "total_duration": total_duration,
    }


def _create_silent_audio(output_file: str, duration: float) -> None:
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-f", "lavfi",
            "-i", "anullsrc=r=22050:cl=mono", "-t", str(duration),
            "-c:a", "pcm_s16le", output_file,
        ],
        capture_output=True, timeout=30, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1000:] or "Could not create silence")


def _get_audio_duration(audio_file: str) -> float:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", audio_file,
            ],
            capture_output=True, timeout=10, text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as exc:
        logger.warning("Could not get duration: %s", exc)
    return 0.0


def _combine_audio_files(scene_files: list, output_file: str) -> None:
    if not scene_files:
        raise ValueError("No audio files to combine")
    concat_file = Path(output_file).parent / f"{Path(output_file).stem}_concat.txt"
    try:
        with open(concat_file, "w", encoding="utf-8") as f:
            for scene in scene_files:
                f.write(f"file '{Path(scene['path']).resolve()}'\n")
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                "-i", str(concat_file), "-c", "copy", output_file,
            ],
            capture_output=True, timeout=120, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr[-1500:] or "Audio combine failed")
    finally:
        concat_file.unlink(missing_ok=True)


def _generate_subtitles(job_id: str, subtitle_entries: list) -> str:
    srt_file = AUDIO_DIR / f"{job_id}_subtitles.srt"
    with open(srt_file, "w", encoding="utf-8") as f:
        for entry in subtitle_entries:
            f.write(f"{entry['index']}\n")
            f.write(f"{entry['start']} --> {entry['end']}\n")
            f.write(f"{entry['scene_title']}\n")
            f.write(f"{entry['text']}\n\n")
    return str(srt_file)


def _format_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
