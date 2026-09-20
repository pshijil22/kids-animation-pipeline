"""
Main orchestration logic for story generation pipeline
Handles flow: prompt → Ollama → JSON validation → save
"""
import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Import modules
from story import generate_story_with_llm, validate_story_json
from tts import generate_narration_from_story
from scenes import generate_scenes
from video import create_video
from youtube import upload_to_youtube

async def generate_story():
    """
    Main pipeline: Generate story and save it.
    
    Returns:
        dict: The generated story (already validated JSON)
    """
    
    # Create timestamp for unique job ID
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Starting story generation job: {job_id}")
    
    # Step 1: Generate raw story from Ollama
    logger.info("Step 1: Calling Ollama LLM")
    raw_story_text = await generate_story_with_llm()
    logger.debug(f"Raw LLM output: {raw_story_text[:200]}...")
    
    # Step 2: Parse and validate JSON
    logger.info("Step 2: Validating JSON structure")
    story = validate_story_json(raw_story_text)
    logger.info(f"Story validated: '{story['title']}'")
    
    # Step 3: Save story to disk
    logger.info("Step 3: Saving story to disk")
    story_dir = Path("/data/stories")
    story_dir.mkdir(parents=True, exist_ok=True)
    
    story_file = story_dir / f"{job_id}_story.json"
    with open(story_file, 'w') as f:
        json.dump(story, f, indent=2)
    logger.info(f"Story saved to: {story_file}")
    
    # Step 4: Generate narration audio and subtitles
    logger.info("Step 4: Generating narration audio")
    audio_data = await generate_narration_from_story(story, job_id)
    logger.info(f"Narration generated: {audio_data['narration_file']}")
    logger.info(f"Subtitles generated: {audio_data['subtitles_file']}")
    
    # Step 5: Generate scene images
    logger.info("Step 5: Generating scene images")
    scene_data = await generate_scenes(story, job_id)
    logger.info(f"Scene images generated: {len(scene_data['scene_images'])} scenes")
    
    # Step 6: Compose video
    logger.info("Step 6: Composing video with FFmpeg")
    video_data = await create_video(story, audio_data, scene_data, job_id)
    logger.info(f"Video created: {video_data['video_file']}")
    
    # Step 7: Upload to YouTube (optional)
    logger.info("Step 7: Uploading to YouTube")
    youtube_metadata = {
        'title': story['title'],
        'description': story['description'],
        'tags': ['children', 'animation', 'educational'],
        'privacy_status': 'private'  # Start with private for safety
    }
    youtube_result = await upload_to_youtube(video_data['video_file'], youtube_metadata)
    logger.info(f"YouTube upload result: {youtube_result['status']}")
    
    # Add metadata
    story['job_id'] = job_id
    story['story_file'] = str(story_file)
    story['narration_file'] = audio_data['narration_file']
    story['subtitles_file'] = audio_data['subtitles_file']
    story['video_file'] = video_data['video_file']
    story['total_duration'] = audio_data['total_duration']
    story['video_size_bytes'] = video_data['size_bytes']
    story['youtube_result'] = youtube_result
    
    logger.info(f"Pipeline complete: story + narration + video + upload")
    
    return story
