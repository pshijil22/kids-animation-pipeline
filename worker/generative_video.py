"""Generative animated-feature renderer using Runway video generation.

This replaces the procedural 2D renderer. Each story scene becomes a generated
cinematic 3D animated-film shot. The previous shot's final frame is used as the
next shot's visual continuity anchor.
"""
import base64
import json
import logging
import os
import subprocess
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
VIDEOS_DIR = DATA_DIR / "videos"
SHOTS_DIR = DATA_DIR / "generated_shots"

RUNWAY_API = "https://api.dev.runwayml.com/v1"
RUNWAY_MODEL = os.getenv("RUNWAY_VIDEO_MODEL", "wan3")
RUNWAY_RESOLUTION = os.getenv("RUNWAY_VIDEO_RESOLUTION", "720p")
RUNWAY_RATIO = os.getenv("RUNWAY_VIDEO_RATIO", "1280:720")
RUNWAY_DURATION = float(os.getenv("RUNWAY_VIDEO_DURATION", "17"))
RUNWAY_POLL_SECONDS = int(os.getenv("RUNWAY_POLL_SECONDS", "8"))
RUNWAY_TIMEOUT_SECONDS = int(os.getenv("RUNWAY_TASK_TIMEOUT", "1800"))
RUNWAY_CONCURRENCY = int(os.getenv("RUNWAY_CONCURRENCY", "1"))

MIN_SECONDS = 1470
MAX_SECONDS = 1830


def _headers():
    token = os.getenv("RUNWAYML_API_SECRET", "").strip()
    if not token:
        raise RuntimeError(
            "RUNWAYML_API_SECRET is required for generative movie rendering. "
            "Add it as a GitHub Actions secret."
        )
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Runway-Version": "2024-11-06",
    }


def _character_bible(story):
    parts = []
    for character in story.get("characters", []):
        parts.append(
            f"{character.get('name', 'Character')}: "
            f"{character.get('species', 'friendly animal')}; "
            f"{character.get('appearance', '')}; "
            f"personality: {character.get('personality', '')}."
        )
    return " ".join(parts)


def _scene_prompt(story, scene, previous_scene=None):
    character_bible = _character_bible(story)
    continuity = scene.get("continuity", "")
    previous = ""
    if previous_scene:
        previous = (
            f" Continue directly from the previous shot: "
            f"{previous_scene.get('title', '')}. "
            f"The previous action was {previous_scene.get('action', '')}. "
        )

    return f"""
Create a high-quality cinematic family animated-feature movie shot for a
children's adventure. Use a polished, dimensional 3D animation aesthetic with
expressive characters, appealing shapes, detailed environments, rich global
lighting, physically believable materials, cinematic depth of field and
professional feature-film composition. Do not imitate or reproduce any specific
studio, franchise, existing character, artist, or copyrighted property.

This is one continuous movie, not a slideshow. Preserve character identity,
wardrobe, proportions, colors, setting logic and visual world across shots.

CHARACTERS:
{character_bible}

STORY:
Episode: {story.get('title', '')}
Lesson: {story.get('lesson', '')}
Scene {scene.get('number')}: {scene.get('title', '')}
Location: {scene.get('location', '')}
Time: {scene.get('time_of_day', '')}
Visual setting: {scene.get('visual_description', '')}
Action: {scene.get('action', '')}
Character actions: {scene.get('character_actions', scene.get('action', ''))}
Props: {scene.get('props', '')}
Emotion: {scene.get('emotion', '')}
Continuity: {continuity}.
Camera direction: {scene.get('camera', '')}
Motion direction: {scene.get('motion', '')}.
{previous}

Animate the exact story action with readable body language and facial emotion.
Use natural secondary motion in hair/fur/clothing, environment and lighting.
Make the camera move intentionally with the dramatic beat. Avoid static
presentation, random character motion, morphing, duplicate characters, text,
logos, subtitles, watermarks, or unexplained scene changes.
""".strip()


def _submit(prompt, first_frame=None):
    payload = {
        "model": RUNWAY_MODEL,
        "promptText": prompt,
        "ratio": RUNWAY_RATIO,
        "resolution": RUNWAY_RESOLUTION,
        "duration": RUNWAY_DURATION,
    }
    if first_frame:
        payload["promptImage"] = first_frame

    response = requests.post(
        f"{RUNWAY_API}/image_to_video",
        headers=_headers(),
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("id"):
        raise RuntimeError(f"Runway did not return a task id: {data}")
    return data["id"]


def _wait(task_id):
    started = time.monotonic()
    while time.monotonic() - started < RUNWAY_TIMEOUT_SECONDS:
        response = requests.get(
            f"{RUNWAY_API}/tasks/{task_id}",
            headers=_headers(),
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        status = data.get("status")
        if status == "SUCCEEDED":
            output = data.get("output") or []
            if not output:
                raise RuntimeError(f"Runway task {task_id} succeeded without output")
            return output[0]
        if status in {"FAILED", "CANCELED"}:
            raise RuntimeError(f"Runway task {task_id} ended with {status}: {data}")
        time.sleep(RUNWAY_POLL_SECONDS)
    raise TimeoutError(f"Runway task {task_id} timed out after {RUNWAY_TIMEOUT_SECONDS}s")


def _download(url, path):
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    path.write_bytes(response.content)


def _last_frame_data_uri(video_path):
    frame = video_path.with_suffix(".last.jpg")
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.15",
            "-i", str(video_path), "-frames:v", "1", "-q:v", "3", str(frame),
        ],
        check=True,
    )
    encoded = base64.b64encode(frame.read_bytes()).decode("ascii")
    frame.unlink(missing_ok=True)
    return f"data:image/jpeg;base64,{encoded}"


def _concat_clips(clips, output):
    list_file = output.with_suffix(".txt")
    list_file.write_text(
        "".join(f"file '{p.resolve()}'\n" for p in clips),
        encoding="utf-8",
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "warning",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", str(output),
        ],
        check=True,
    )
    list_file.unlink(missing_ok=True)


async def generate_scenes(story, job_id):
    """Generate the movie shots and return their metadata."""
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    scenes = story.get("scenes", [])
    if not scenes:
        raise ValueError("Story contains no scenes")

    clips = []
    metadata = []
    previous_scene = None
    first_frame = None

    # Sequential generation is intentional: each shot feeds its final frame
    # into the next shot so the episode behaves like one continuous movie.
    for index, scene in enumerate(scenes, 1):
        prompt = _scene_prompt(story, scene, previous_scene)
        logger.info("Generating cinematic shot %s/%s with %s...", index, len(scenes), RUNWAY_MODEL)
        task_id = _submit(prompt, first_frame)
        logger.info("Runway task %s started for scene %s", task_id, index)
        url = _wait(task_id)

        clip = SHOTS_DIR / f"{job_id}_shot_{index:03d}.mp4"
        _download(url, clip)
        clips.append(clip)
        metadata.append({
            "number": int(scene.get("number", index)),
            "path": str(clip),
            "prompt": prompt,
            "runway_task_id": task_id,
        })

        first_frame = _last_frame_data_uri(clip)
        previous_scene = scene

    manifest = SHOTS_DIR / f"{job_id}_shots.json"
    manifest.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"scene_images": metadata, "clips": clips}


async def create_animated_video(story, audio_data, scene_data, job_id):
    """Assemble generated movie shots with the existing narration/subtitles."""
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    clips = [Path(p) for p in scene_data.get("clips", [])]
    if not clips:
        raise ValueError("No generated movie clips were produced")

    narration = Path(audio_data["narration_file"])
    subtitles = Path(audio_data["subtitles_file"])
    if not narration.exists():
        raise FileNotFoundError(narration)

    output = VIDEOS_DIR / f"{job_id}.mp4"
    silent_movie = VIDEOS_DIR / f"{job_id}_generated.mp4"
    _concat_clips(clips, silent_movie)

    # Generated shots are the movie. Fit them to the narration duration and
    # finish at the requested 1080p delivery size.
    subtitle_path = str(subtitles.resolve()).replace(chr(92), "/").replace(":", "\:").replace(chr(39), "\'")
    subtitle_filter = (
        f"subtitles='{subtitle_path}':force_style="
        "'FontName=DejaVu Sans,FontSize=22,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H001B1630,BorderStyle=3,Outline=2,Shadow=1,MarginV=34'"
    )

    cmd = [
        "ffmpeg", "-y", "-loglevel", "warning",
        "-i", str(silent_movie), "-i", str(narration),
        "-filter_complex",
        f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,"
        f"crop=1920:1080,eq=contrast=1.04:saturation=1.08:gamma=1.01,"
        f"unsharp=5:5:0.25:5:5:0.0,{subtitle_filter}[v]",
        "-map", "[v]", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", os.getenv("VIDEO_PRESET", "slow"),
        "-crf", os.getenv("VIDEO_CRF", "18"), "-c:a", "aac", "-b:a", "160k",
        "-ar", "48000", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-shortest", str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    if result.returncode != 0:
        logger.error(result.stderr[-5000:])
        raise RuntimeError("Final generative movie assembly failed")

    duration = float(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(output)],
            text=True,
        ).strip()
    )
    if not MIN_SECONDS <= duration <= MAX_SECONDS:
        raise RuntimeError(f"Generated movie duration is {duration:.1f}s; expected 25-30 minutes")

    size = output.stat().st_size
    if size < 100_000:
        raise RuntimeError(f"Video output is suspiciously small: {size} bytes")

    silent_movie.unlink(missing_ok=True)
    return {
        "video_file": str(output),
        "title": story["title"],
        "description": story["description"],
        "size_bytes": size,
        "duration_seconds": duration,
        "job_id": job_id,
        "resolution": "1920x1080",
        "fps": 30,
    }
