"""Local neural narration using Piper, with eSpeak only as a last-resort fallback."""
import os
import shutil
import subprocess
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
AUDIO_DIR = DATA_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
TARGET = float(os.getenv("CINEMATIC_SCENE_SECONDS", "16.5"))
PIPER_MODEL = os.getenv("PIPER_MODEL", "en_US-lessac-high")
VOICE = os.getenv("TTS_VOICE", "en-us")


def _duration(path):
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return float(r.stdout.strip()) if r.stdout.strip() else 0.0


def _speak(text, out):
    piper = shutil.which("piper")
    if piper:
        r = subprocess.run(
            [
                piper,
                "--model",
                PIPER_MODEL,
                "--output_file",
                str(out),
                "--length_scale",
                os.getenv("PIPER_LENGTH_SCALE", "1.0"),
                "--noise_scale",
                os.getenv("PIPER_NOISE_SCALE", "0.667"),
                "--noise_w",
                os.getenv("PIPER_NOISE_W", "0.333"),
            ],
            input=text,
            text=True,
            capture_output=True,
            timeout=180,
        )
        if r.returncode == 0 and out.exists() and out.stat().st_size > 1000:
            return
    binary = shutil.which("espeak-ng") or shutil.which("espeak")
    if not binary:
        raise RuntimeError("Piper TTS failed and espeak-ng is not installed")
    r = subprocess.run(
        [binary, "-v", VOICE, "-s", "145", "-p", "52", "-w", str(out), text],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode:
        raise RuntimeError(r.stderr[-1500:] or "TTS failed")


async def generate_narration_from_story(story, job_id):
    files = []
    entries = []
    total = 0.0
    for i, sc in enumerate(story.get("scenes", []), 1):
        text = (sc.get("narration") or "").strip() or "Let's see what happens next."
        wav = AUDIO_DIR / (f"{job_id}_scene_{i:03d}.wav")
        _speak(text, wav)
        spoken = _duration(str(wav))
        if spoken <= 0:
            raise RuntimeError(f"Invalid narration for scene {i}")
        if spoken > TARGET or spoken < TARGET * 0.80:
            tempo = spoken / TARGET
            factors = []
            while tempo > 2:
                factors.append("2.0")
                tempo /= 2
            while tempo < 0.5:
                factors.append("0.5")
                tempo /= 0.5
            factors.append(f"{tempo:.6f}")
            af = ",".join("atempo=" + x for x in factors) + (
                f",apad,atrim=duration={TARGET:.3f}"
            )
        else:
            af = f"apad,atrim=duration={TARGET:.3f}"
        out = wav.with_suffix(".pad.wav")
        r = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                str(wav),
                "-af",
                af,
                "-ar",
                "22050",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(out),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r.returncode:
            raise RuntimeError(r.stderr[-1000:] or "Narration normalization failed")
        out.replace(wav)
        files.append(str(wav))
        entries.append(
            (i, total, min(spoken, TARGET), sc.get("title", f"Scene {i}"), text[:220])
        )
        total += TARGET

    concat = AUDIO_DIR / f"{job_id}_concat.txt"
    with concat.open("w", encoding="utf-8") as f:
        for p in files:
            f.write(f"file '{Path(p).resolve()}'\n")
    narration = AUDIO_DIR / f"{job_id}_narration.wav"
    r = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-c",
            "copy",
            str(narration),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    concat.unlink(missing_ok=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-1000:] or "Audio combine failed")

    srt = AUDIO_DIR / f"{job_id}_subtitles.srt"
    with srt.open("w", encoding="utf-8") as f:
        for idx, start, spoken, title, text in entries:
            f.write(f"{idx}\n{_srt(start)} --> {_srt(start + spoken)}\n{title}\n{text}\n\n")
    return {
        "narration_file": str(narration),
        "subtitles_file": str(srt),
        "scene_narrations": files,
        "total_duration": total,
    }


def _srt(x):
    h = int(x // 3600)
    m = int((x % 3600) // 60)
    s = int(x % 60)
    ms = int((x % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
