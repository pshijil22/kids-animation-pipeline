"""
Main orchestration logic for YouTube-quality video generation pipeline
Optimized for GitHub Actions: Fast, no GPU required
Flow: Story → High-quality Scenes → Professional Audio → Animated Video
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
from scenes import generate_scenes
from tts import generate_narration_from_story
from blender_animation import create_animated_video
from youtube import upload_to_youtube

# Use environment variable for data directory
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))


async def generate_story():
    """
    Main pipeline: Generate YouTube-quality animated video
    Optimized for GitHub Actions (fast, no GPU needed)
    
    Flow:
    1. Generate story with Ollama LLM
    2. Generate colorful Pillow scenes (fast, no SD needed)
    3. Generate narration with eSpeak (free, fast)
    4. Create animated video with Ken Burns effects
    5. Upload to YouTube (optional)
    
    Returns:
        dict: The generated story with video metadata
    """
    
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Starting YouTube-quality video generation job: {job_id}")
    
    # Step 1: Generate story
    logger.info("Step 1: Generating story with Ollama LLM...")
    raw_story_text = await generate_story_with_llm()
    story = validate_story_json(raw_story_text)
    logger.info(f"Story: '{story['title']}'")
    
    # Save story
    story_dir = DATA_DIR / 'stories'
    story_dir.mkdir(parents=True, exist_ok=True)
    story_file = story_dir / f"{job_id}_story.json"
    with open(story_file, 'w') as f:
        json.dump(story, f, indent=2)
    
    # Step 2: Generate colorful scenes (fast)
    logger.info("Step 2: Generating colorful animated scenes...")
    scene_data = await generate_scenes(story, job_id)
    logger.info(f"Scenes: {len(scene_data['scene_images'])} generated")
    
    # Step 3: Generate narration
    logger.info("Step 3: Generating narration audio...")
    audio_data = await generate_narration_from_story(story, job_id)
    logger.info(f"Narration: {audio_data['total_duration']:.1f}s")
    
    # Step 4: Create animated video
    logger.info("Step 4: Creating animated video with Ken Burns effects...")
    video_data = await create_animated_video(story, audio_data, scene_data, job_id)
    logger.info(f"Video: {video_data['resolution']} @ {video_data['fps']} FPS")
    
    # Step 5: Upload to YouTube (optional)
    logger.info("Step 5: YouTube upload (optional)...")
    youtube_metadata = {
        'title': story['title'],
        'description': story['description'],
        'tags': ['animation', 'children', 'educational'],
        'privacy_status': 'private'
    }
    youtube_result = await upload_to_youtube(video_data['video_file'], youtube_metadata)
    logger.info(f"YouTube: {youtube_result['status']}")
    
    # Compile final metadata
    story['job_id'] = job_id
    story['story_file'] = str(story_file)
    story['narration_file'] = audio_data['narration_file']
    story['subtitles_file'] = audio_data['subtitles_file']
    story['video_file'] = video_data['video_file']
    story['video_resolution'] = video_data['resolution']
    story['video_fps'] = video_data['fps']
    story['total_duration'] = audio_data['total_duration']
    story['video_size_bytes'] = video_data['size_bytes']
    story['youtube_result'] = youtube_result
    story['quality_level'] = 'youtube_ready'
    
    logger.info(f"✅ COMPLETE: {story['title']}")
    logger.info(f"   Video: {video_data['size_bytes'] / 1024 / 1024:.1f}MB, {video_data['resolution']}")
    
    return story
