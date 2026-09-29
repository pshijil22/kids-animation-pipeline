"""
Single orchestration entry point for the automated kids animation pipeline.

Flow: story acts -> narration -> 2D scenes -> animated MP4 -> optional YouTube upload.
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from story import generate_story_with_llm, validate_story_json
from blender_animation import generate_scenes, create_animated_video
from tts import generate_narration_from_story
from youtube import upload_to_youtube

logger = logging.getLogger(__name__)
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))


async def generate_story():
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("Starting episode build: %s", job_id)

    logger.info("1/4 Generating five-act story...")
    story = validate_story_json(await generate_story_with_llm())

    story_dir = DATA_DIR / "stories"
    story_dir.mkdir(parents=True, exist_ok=True)
    story_file = story_dir / f"{job_id}_story.json"
    story_file.write_text(json.dumps(story, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info("2/4 Generating 100 illustrated scenes...")
    scene_data = await generate_scenes(story, job_id)

    logger.info("3/4 Generating narration...")
    audio_data = await generate_narration_from_story(story, job_id)
    logger.info("Narration duration: %.1fs", audio_data["total_duration"])

    logger.info("4/4 Rendering final 1080p episode...")
    video_data = await create_animated_video(story, audio_data, scene_data, job_id)

    upload_enabled = os.getenv("YOUTUBE_UPLOAD", "false").lower() == "true"
    if upload_enabled:
        youtube_result = await upload_to_youtube(
            video_data["video_file"],
            {
                **story,
                "privacy_status": os.getenv("YOUTUBE_PRIVACY", "private"),
            },
        )
    else:
        youtube_result = {
            "status": "not_uploaded",
            "reason": "YOUTUBE_UPLOAD is not enabled.",
        }

    story.update(
        {
            "job_id": job_id,
            "story_file": str(story_file),
            "narration_file": audio_data["narration_file"],
            "subtitles_file": audio_data["subtitles_file"],
            "video_file": video_data["video_file"],
            "video_resolution": video_data["resolution"],
            "video_fps": video_data["fps"],
            "total_duration": audio_data["total_duration"],
            "video_size_bytes": video_data["size_bytes"],
            "youtube_result": youtube_result,
            "quality_level": "youtube_ready",
        }
    )
    logger.info("COMPLETE: %s", story["title"])
    return story
