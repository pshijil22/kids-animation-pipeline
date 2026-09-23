"""
Main orchestration logic for high-quality video generation pipeline
Handles flow: Story → AI Scenes → Professional Audio → Animated Video → Music
"""
import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Import new high-quality modules
from story import generate_story_with_llm, validate_story_json
from ai_scenes import generate_ai_scenes
from professional_tts import generate_professional_narration
from blender_animation import create_animated_video
from music import add_background_music
from youtube import upload_to_youtube

# Use environment variable for data directory
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))


async def generate_story():
    """
    Main pipeline: Generate high-quality animated video
    
    Flow:
    1. Generate story with Ollama LLM
    2. Generate AI scenes with Stable Diffusion
    3. Generate professional narration with Google Cloud TTS
    4. Create animated video with Ken Burns effects
    5. Add background music (optional)
    6. Upload to YouTube (optional)
    
    Returns:
        dict: The generated story with video metadata
    """
    
    # Create timestamp for unique job ID
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Starting high-quality video generation job: {job_id}")
    
    # Step 1: Generate raw story from Ollama
    logger.info("Step 1: Generating story with Ollama LLM...")
    raw_story_text = await generate_story_with_llm()
    logger.debug(f"Raw LLM output: {raw_story_text[:200]}...")
    
    # Step 2: Parse and validate JSON
    logger.info("Step 2: Validating story structure...")
    story = validate_story_json(raw_story_text)
    logger.info(f"Story validated: '{story['title']}'")
    
    # Step 3: Save story to disk
    logger.info("Step 3: Saving story metadata...")
    story_dir = DATA_DIR / 'stories'
    story_dir.mkdir(parents=True, exist_ok=True)
    
    story_file = story_dir / f"{job_id}_story.json"
    with open(story_file, 'w') as f:
        json.dump(story, f, indent=2)
    logger.info(f"Story saved to: {story_file}")
    
    # Step 4: Generate AI scenes with Stable Diffusion
    logger.info("Step 4: Generating AI scenes with Stable Diffusion...")
    try:
        scene_data = await generate_ai_scenes(story, job_id)
        logger.info(f"AI scenes generated: {len(scene_data['scene_images'])} scenes")
    except Exception as e:
        logger.warning(f"AI scene generation failed, using fallback: {e}")
        # Fallback to simple scenes if SD unavailable
        from scenes import generate_scenes
        scene_data = await generate_scenes(story, job_id)
    
    # Step 5: Generate professional narration
    logger.info("Step 5: Generating professional narration...")
    try:
        audio_data = await generate_professional_narration(story, job_id)
        logger.info(f"Narration generated: {audio_data['narration_file']}")
    except Exception as e:
        logger.warning(f"Professional TTS failed, using fallback: {e}")
        # Fallback to eSpeak if GCP TTS unavailable
        from tts import generate_narration_from_story
        audio_data = await generate_narration_from_story(story, job_id)
    
    logger.info(f"Subtitles generated: {audio_data['subtitles_file']}")
    
    # Step 6: Create animated video with Ken Burns effects
    logger.info("Step 6: Creating animated video...")
    video_data = await create_animated_video(story, audio_data, scene_data, job_id)
    logger.info(f"Animated video created: {video_data['video_file']}")
    logger.info(f"Resolution: {video_data['resolution']}, {video_data['fps']} FPS")
    
    # Step 7: Add background music (optional)
    logger.info("Step 7: Adding background music...")
    try:
        video_with_music = await add_background_music(
            video_file=video_data['video_file'],
            audio_file=audio_data['narration_file'],
            total_duration=audio_data['total_duration'],
            job_id=job_id
        )
        video_data['video_file'] = video_with_music
        logger.info(f"Background music added (if available)")
    except Exception as e:
        logger.warning(f"Background music addition skipped: {e}")
    
    # Step 8: Upload to YouTube (optional)
    logger.info("Step 8: Uploading to YouTube...")
    youtube_metadata = {
        'title': story['title'],
        'description': story['description'],
        'tags': ['animation', 'children', 'educational', 'AI-generated'],
        'privacy_status': 'private'  # Start with private for safety
    }
    youtube_result = await upload_to_youtube(video_data['video_file'], youtube_metadata)
    logger.info(f"YouTube upload result: {youtube_result['status']}")
    
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
    story['quality_level'] = 'professional'
    
    logger.info(f"✅ PIPELINE COMPLETE: High-quality animated video generated!")
    logger.info(f"   Story: {story['title']}")
    logger.info(f"   Video: {video_data['video_file']}")
    logger.info(f"   Size: {video_data['size_bytes'] / 1024 / 1024:.1f} MB")
    logger.info(f"   Duration: {audio_data['total_duration']:.1f}s")
    logger.info(f"   Ready for YouTube: {youtube_result['status'] == 'success'}")
    
    return story
