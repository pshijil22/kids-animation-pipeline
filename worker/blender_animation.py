"""Procedural 2D scene renderer and FFmpeg compositor for the kids animation pipeline."""
import hashlib
import json
import logging
import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

logger = logging.getLogger(__name__)
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
SCENES_DIR = DATA_DIR / "scenes"
VIDEOS_DIR = DATA_DIR / "videos"
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1920"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1080"))
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))
VIDEO_CRF = os.getenv("VIDEO_CRF", "18")
VIDEO_PRESET = os.getenv("VIDEO_PRESET", "slow")
MIN_SECONDS = 1470
MAX_SECONDS = 1830

PALETTES = [
    ("#8ED8FF", "#C9F7A8", "#FDE68A"),
    ("#B8A7FF", "#BDE7A5", "#FFD6A5"),
    ("#9EE7D7", "#D7F9B0", "#FFE7A8"),
]


def _seed(scene):
    return int(hashlib.sha256(scene.get("visual_description", "").encode()).hexdigest()[:8], 16)


def _gradient(draw, top, bottom):
    def rgb(value):
        value = value.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    a, b = rgb(top), rgb(bottom)
    for y in range(VIDEO_HEIGHT):
        t = y / max(1, VIDEO_HEIGHT - 1)
        c = tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))
        draw.line((0, y, VIDEO_WIDTH, y), fill=c)


def _character(draw, cx, ground, kind, scale=1.0, bob=0):
    s = scale
    cy = ground - int(150 * s) + int(bob)
    body = {
        "rabbit": "#F6A6B2",
        "fox": "#F4B860",
        "owl": "#9B8AFB",
        "bear": "#8EC5FF",
    }.get(kind, "#F7C948")
    outline = "#493B5A"
    draw.ellipse(
        (cx - int(70 * s), ground - int(10 * s), cx + int(70 * s), ground + int(15 * s)),
        fill="#00000020",
    )
    if kind == "owl":
        draw.ellipse(
            (cx - int(58 * s), cy - int(45 * s), cx + int(58 * s), cy + int(65 * s)),
            fill=body, outline=outline, width=max(1, int(4 * s)),
        )
        for side in (-1, 1):
            draw.ellipse(
                (cx + int(side * 45 * s) - int(25 * s), cy - int(65 * s),
                 cx + int(side * 45 * s) + int(20 * s), cy - int(5 * s)),
                fill=body, outline=outline, width=max(1, int(4 * s)),
            )
        for ex in (-24, 24):
            draw.ellipse(
                (cx + int((ex - 15) * s), cy - int(42 * s),
                 cx + int((ex + 15) * s), cy - int(12 * s)),
                fill="white", outline=outline, width=max(1, int(3 * s)),
            )
            draw.ellipse(
                (cx + int((ex - 5) * s), cy - int(35 * s),
                 cx + int((ex + 5) * s), cy - int(25 * s)), fill=outline,
            )
        draw.polygon(
            [(cx - int(10 * s), cy - int(3 * s)), (cx + int(10 * s), cy - int(3 * s)),
             (cx, cy + int(12 * s))], fill="#F7C948",
        )
    else:
        draw.ellipse(
            (cx - int(52 * s), cy - int(35 * s), cx + int(52 * s), cy + int(70 * s)),
            fill=body, outline=outline, width=max(1, int(4 * s)),
        )
        if kind == "rabbit":
            for side in (-1, 1):
                draw.ellipse(
                    (cx + int(side * 25 * s) - int(15 * s), cy - int(105 * s),
                     cx + int(side * 25 * s) + int(15 * s), cy - int(25 * s)),
                    fill=body, outline=outline, width=max(1, int(4 * s)),
                )
        elif kind == "fox":
            draw.polygon(
                [(cx - int(55 * s), cy - int(25 * s)),
                 (cx - int(35 * s), cy - int(90 * s)), (cx, cy - int(55 * s)),
                 (cx + int(35 * s), cy - int(90 * s)),
                 (cx + int(55 * s), cy - int(25 * s))],
                fill=body, outline=outline,
            )
        else:
            draw.ellipse(
                (cx - int(58 * s), cy - int(75 * s), cx + int(58 * s), cy + int(25 * s)),
                fill=body, outline=outline, width=max(1, int(4 * s)),
            )
        for ex in (-20, 20):
            draw.ellipse(
                (cx + int((ex - 5) * s), cy - int(25 * s),
                 cx + int((ex + 5) * s), cy - int(15 * s)), fill=outline,
            )
        draw.arc(
            (cx - int(18 * s), cy - int(10 * s), cx + int(18 * s), cy + int(18 * s)),
            0, 180, fill=outline, width=max(1, int(3 * s)),
        )
    draw.line(
        (cx - int(45 * s), cy + int(25 * s), cx - int(75 * s), cy + int(5 * s)),
        fill=outline, width=max(2, int(6 * s)),
    )
    draw.line(
        (cx + int(45 * s), cy + int(25 * s), cx + int(75 * s), cy + int(5 * s)),
        fill=outline, width=max(2, int(6 * s)),
    )


def _kind(text):
    t = text.lower()
    for word in ("owl", "rabbit", "bunny", "fox", "bear", "cat", "dog", "bird"):
        if word in t:
            return "rabbit" if word == "bunny" else ("bear" if word in ("cat", "dog", "bird") else word)
    return "bear"


def _create_scene_image(scene, character_kind=None):
    description = (scene.get("visual_description") or "").strip()
    action = (scene.get("action") or "").strip()
    seed = _seed(scene)
    sky, grass, sun = PALETTES[seed % len(PALETTES)]
    image = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(image)
    _gradient(draw, sky, "#FFF4D6")

    horizon = int(VIDEO_HEIGHT * 0.60)
    draw.polygon(
        [(0, horizon), (220, horizon - 130), (430, horizon),
         (650, horizon - 150), (900, horizon), (1110, horizon - 130),
         (VIDEO_WIDTH, horizon), (VIDEO_WIDTH, VIDEO_HEIGHT), (0, VIDEO_HEIGHT)],
        fill="#A8DFA8",
    )
    draw.rectangle((0, horizon, VIDEO_WIDTH, VIDEO_HEIGHT), fill=grass)
    draw.ellipse((VIDEO_WIDTH - 190, 55, VIDEO_WIDTH - 70, 175), fill=sun)

    for x in (120, 470, 820, 1180, 1540):
        y = 90 + (seed + x) % 45
        for dx, dy, r in ((0, 12, 42), (45, 0, 52), (88, 14, 38)):
            draw.ellipse((x + dx - r, y + dy - r, x + dx + r, y + dy + r), fill="#FFFFFF")

    lower = (description + " " + action).lower()
    has_tree = any(word in lower for word in ("tree", "forest", "garden"))
    tree_x = [110, VIDEO_WIDTH - 150] if has_tree else [90, VIDEO_WIDTH - 110]
    for x in tree_x:
        draw.rectangle((x - 18, horizon - 145, x + 18, horizon + 15), fill="#8B5A3C")
        draw.ellipse((x - 75, horizon - 225, x + 75, horizon - 85), fill="#4FAF62", outline="#397B49", width=4)
        draw.ellipse((x - 55, horizon - 260, x + 55, horizon - 130), fill="#62BF6F", outline="#397B49", width=4)

    if "flower" in lower or "garden" in lower:
        for x in range(260, min(VIDEO_WIDTH - 50, 1500), 110):
            draw.line((x, horizon + 15, x, horizon - 25), fill="#3F8C45", width=4)
            draw.ellipse((x - 12, horizon - 40, x + 2, horizon - 26), fill="#FF7BA5")
            draw.ellipse((x + 1, horizon - 40, x + 15, horizon - 26), fill="#FFD166")

    if "path" in lower or "road" in lower:
        draw.polygon(
            [(VIDEO_WIDTH // 2 - 35, VIDEO_HEIGHT), (VIDEO_WIDTH // 2 + 35, VIDEO_HEIGHT),
             (VIDEO_WIDTH // 2 + 170, horizon), (VIDEO_WIDTH // 2 - 170, horizon)],
            fill="#E7CFA3",
        )

    # Semantic action changes position/pose slightly so consecutive scenes are not identical.
    direction = -1 if seed % 2 else 1
    cx = VIDEO_WIDTH // 2 + ((seed % 9) - 4) * 55
    ground = int(VIDEO_HEIGHT * 0.73)
    _character(draw, cx, ground, character_kind or _kind(description + " " + action), 1.15, 0)

    for i in range(16):
        x = (seed * (i + 3) * 17) % VIDEO_WIDTH
        y = VIDEO_HEIGHT - ((seed * (i + 5) * 11) % 180)
        draw.ellipse((x, y, x + 18, y + 8), fill="#5BAE63")

    return image.filter(ImageFilter.SMOOTH)


async def generate_scenes(story: dict, job_id: str) -> dict:
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    scene_images = []
    character_text = json.dumps(story.get("characters", []), ensure_ascii=False)
    primary_kind = _kind(character_text)
    for i, scene in enumerate(story.get("scenes", []), 1):
        number = int(scene.get("number", i))
        path = SCENES_DIR / f"{job_id}_scene_{number:03d}.png"
        try:
            _create_scene_image(scene, primary_kind).save(path, "PNG", optimize=True)
        except Exception:
            logger.exception("Scene %s failed; creating fallback", number)
            Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), "#9DDCFF").save(path, "PNG")
        scene_images.append({"number": number, "path": str(path), "description": scene.get("visual_description", "")})
    return {"scene_images": scene_images}


def _scene_durations(story, audio_data, scene_images):
    actual = audio_data.get("scene_narrations") or []
    by_num = {
        int(x.get("scene_num", i + 1)): float(x.get("duration", 0) or 0)
        for i, x in enumerate(actual)
    }
    fallback = float(audio_data.get("total_duration", story.get("duration_seconds", 60)) or 60) / max(1, len(scene_images))
    durations = [max(2.0, by_num.get(int(s.get("number", i + 1)), fallback)) for i, s in enumerate(scene_images)]
    total = sum(durations)
    if not MIN_SECONDS <= total <= MAX_SECONDS:
        raise ValueError(f"Episode duration is {total:.1f}s; expected 25-30 minutes")
    return durations


def _subtitle_filter(path):
    value = str(Path(path).resolve()).replace(chr(92), "/").replace(":", "\:").replace(chr(39), "\'")
    return (
        f"subtitles='{value}':force_style="
        "'FontName=DejaVu Sans,FontSize=22,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H001B1630,BorderStyle=3,Outline=2,Shadow=1,MarginV=34'"
    )


async def create_animated_video(story, audio_data, scene_data, job_id):
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    images = scene_data.get("scene_images", [])
    if not images:
        raise ValueError("No scene images were generated")
    narration = Path(audio_data["narration_file"])
    subtitles = Path(audio_data["subtitles_file"])
    if not narration.exists():
        raise FileNotFoundError(narration)

    durations = _scene_durations(story, audio_data, images)
    output = VIDEOS_DIR / f"{job_id}.mp4"
    inputs = []
    filters = []

    for i, (scene, duration) in enumerate(zip(images, durations)):
        path = Path(scene["path"])
        if not path.exists():
            raise FileNotFoundError(path)
        frames = max(1, round(duration * VIDEO_FPS))
        if i % 4 == 0:
            z, x = "min(zoom+0.00055,1.10)", "iw/2-(iw/zoom/2)"
        elif i % 4 == 1:
            z, x = "max(1.0,zoom-0.00035)", "iw/2-(iw/zoom/2)-20"
        elif i % 4 == 2:
            z, x = "min(zoom+0.00045,1.08)", f"(iw-iw/zoom)*on/{frames}"
        else:
            z, x = "min(zoom+0.00045,1.08)", f"(iw-iw/zoom)*(1-on/{frames})"

        inputs += ["-loop", "1", "-t", f"{duration:.3f}", "-i", str(path)]
        filters.append(
            f"[{i}:v]scale={VIDEO_WIDTH * 2}:{VIDEO_HEIGHT * 2}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH * 2}:{VIDEO_HEIGHT * 2},"
            f"zoompan=z='{z}':x='{x}':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},setsar=1[v{i}]"
        )

    filters.append("".join(f"[v{i}]" for i in range(len(images))) + f"concat=n={len(images)}:v=1:a=0[v]")
    filters.append(f"[v]{_subtitle_filter(subtitles)}[vout]")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "warning", *inputs, "-i", str(narration),
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", f"{len(images)}:a:0",
        "-c:v", "libx264", "-preset", VIDEO_PRESET, "-crf", VIDEO_CRF,
        "-tune", "animation", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-shortest", str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    if result.returncode != 0:
        logger.error(result.stderr[-4000:])
        raise RuntimeError("FFmpeg animation render failed")

    size = output.stat().st_size
    if size < 100_000:
        raise RuntimeError(f"Video output is suspiciously small: {size} bytes")
    return {
        "video_file": str(output),
        "title": story["title"],
        "description": story["description"],
        "size_bytes": size,
        "duration_seconds": sum(durations),
        "job_id": job_id,
        "resolution": f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
        "fps": VIDEO_FPS,
    }
