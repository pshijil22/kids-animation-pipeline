"""Automated story -> cinematic preview/full render -> optional YouTube upload."""
import asyncio
import copy
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from story import generate_story_with_llm, validate_story_json
from generative_video import generate_scenes, create_animated_video
from tts import generate_narration_from_story
from youtube import upload_to_youtube

logger=logging.getLogger(__name__)
DATA_DIR=Path(os.getenv("DATA_DIR","./data"))
PREVIEW=os.getenv("CINEMATIC_PREVIEW","true").lower()=="true"
PREVIEW_SCENES=int(os.getenv("CINEMATIC_PREVIEW_SCENES","6"))

async def generate_story():
    job_id=datetime.now().strftime("%Y%m%d_%H%M%S")
    story=validate_story_json(await generate_story_with_llm())
    d=DATA_DIR/"stories"
    d.mkdir(parents=True,exist_ok=True)
    sf=d/("%s_story.json"%job_id)
    sf.write_text(json.dumps(story,indent=2,ensure_ascii=False),encoding="utf-8")

    production=copy.deepcopy(story)
    if PREVIEW:
        production["scenes"]=production["scenes"][:PREVIEW_SCENES]
        production["duration_seconds"]=PREVIEW_SCENES*15
        production["target_duration_seconds"]=PREVIEW_SCENES*15
        logger.info("CINEMATIC PROOF: first %s scenes, about 90 seconds",PREVIEW_SCENES)

    scene_data=await generate_scenes(production,job_id)
    audio_data=await generate_narration_from_story(production,job_id)
    video_data=await create_animated_video(production,audio_data,scene_data,job_id)

    if os.getenv("YOUTUBE_UPLOAD","false").lower()=="true":
        youtube_result=await upload_to_youtube(
            video_data["video_file"],
            {**story,"privacy_status":os.getenv("YOUTUBE_PRIVACY","private")})
    else:
        youtube_result={"status":"not_uploaded","reason":"YOUTUBE_UPLOAD is not enabled."}

    story.update({
        "job_id":job_id,
        "story_file":str(sf),
        "narration_file":audio_data["narration_file"],
        "subtitles_file":audio_data["subtitles_file"],
        "video_file":video_data["video_file"],
        "video_resolution":video_data["resolution"],
        "video_fps":video_data["fps"],
        "total_duration":video_data["duration_seconds"],
        "video_size_bytes":video_data["size_bytes"],
        "youtube_result":youtube_result,
        "quality_level":"cinematic_proof" if PREVIEW else "youtube_ready",
    })
    logger.info("COMPLETE: %s",story["title"])
    return story
