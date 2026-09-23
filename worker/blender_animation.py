"""
Blender Animation Engine
Creates smooth, professional animations using Blender
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# Use environment variable for data directory
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
VIDEOS_DIR = DATA_DIR / 'videos'

# Blender settings
BLENDER_EXECUTABLE = os.getenv('BLENDER_EXECUTABLE', 'blender')
VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', 1920))
VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', 1080))
VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))


async def create_animated_video(story: dict, audio_data: dict, scene_data: dict, job_id: str) -> dict:
    """
    Create professional animated video using Blender.
    
    Args:
        story: Story metadata
        audio_data: Audio files (narration_file, subtitles_file, total_duration)
        scene_data: Scene images (scene_images list)
        job_id: Unique job ID
    
    Returns:
        dict: Contains video_file path and metadata
    """
    
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Creating animated video for job {job_id}")
    logger.info(f"Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} @ {VIDEO_FPS} FPS")
    
    try:
        narration_file = audio_data['narration_file']
        subtitles_file = audio_data['subtitles_file']
        scene_images = scene_data['scene_images']
        total_duration = audio_data['total_duration']
        
        output_file = VIDEOS_DIR / f"{job_id}.mp4"
        
        # Create animated slideshow with Ken Burns effect
        video_path = _create_ken_burns_video(
            scene_images=scene_images,
            total_duration=total_duration,
            output_file=str(output_file),
            job_id=job_id
        )
        
        # Add audio and subtitles with FFmpeg
        final_video = _add_audio_subtitles(
            video_file=video_path,
            audio_file=narration_file,
            subtitles_file=subtitles_file,
            output_file=str(output_file),
            job_id=job_id
        )
        
        logger.info(f"Animated video created: {final_video}")
        
        file_size = Path(final_video).stat().st_size
        logger.info(f"Video size: {file_size / 1024 / 1024:.2f} MB")
        
        return {
            'video_file': str(final_video),
            'title': story['title'],
            'description': story['description'],
            'size_bytes': file_size,
            'duration_seconds': total_duration,
            'job_id': job_id,
            'resolution': f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
            'fps': VIDEO_FPS
        }
        
    except Exception as e:
        logger.error(f"Animated video creation failed: {e}")
        raise


def _create_ken_burns_video(scene_images: list, total_duration: float, output_file: str, job_id: str) -> str:
    """
    Create video with Ken Burns effect (zoom/pan on static images).
    Uses FFmpeg for fast generation.
    """
    import subprocess
    
    logger.info("Creating video with Ken Burns effect...")
    
    duration_per_scene = total_duration / len(scene_images)
    
    # Create FFmpeg filter complex for Ken Burns effect
    filter_complex = _build_ken_burns_filter(scene_images, duration_per_scene)
    
    # Use intermediate format for processing
    intermediate_file = VIDEOS_DIR / f"{job_id}_intermediate.mp4"
    
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", str(VIDEO_FPS),
    ]
    
    # Add all images as inputs
    for scene in scene_images:
        cmd.extend(["-loop", "1", "-t", str(duration_per_scene), "-i", scene['path']])
    
    cmd.extend([
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        str(intermediate_file)
    ])
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=600, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg failed: {result.stderr}")
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        logger.info(f"Video with Ken Burns effect created: {intermediate_file}")
        return str(intermediate_file)
        
    except Exception as e:
        logger.error(f"Failed to create Ken Burns video: {e}")
        raise


def _build_ken_burns_filter(scene_images: list, duration_per_scene: float) -> str:
    """
    Build FFmpeg filter complex for Ken Burns effect.
    Ken Burns: slowly zoom in and pan across image.
    """
    filters = []
    
    for i, scene in enumerate(scene_images):
        # Scale and apply zoom/pan effect
        scale_w = VIDEO_WIDTH
        scale_h = VIDEO_HEIGHT
        
        # Ken Burns zoom (20% zoom over duration)
        # Start: 1.0x, End: 1.2x
        filter_str = f"[{i}:v]scale={scale_w}:{scale_h},zoompan=z='min(zoom+0.0015,1.2)':d={int(duration_per_scene * VIDEO_FPS)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'[v{i}]"
        filters.append(filter_str)
    
    # Concatenate all filtered images
    concat_inputs = ''.join([f'[v{i}]' for i in range(len(scene_images))])
    concat_filter = f"{concat_inputs}concat=n={len(scene_images)}:v=1:a=0[v]"
    
    full_filter = ";".join(filters) + ";" + concat_filter
    
    return full_filter


def _add_audio_subtitles(video_file: str, audio_file: str, subtitles_file: str, output_file: str, job_id: str) -> str:
    """
    Add audio and subtitles to video using FFmpeg.
    """
    import subprocess
    
    logger.info("Adding audio and subtitles...")
    
    audio_abs = Path(audio_file).resolve()
    subtitles_abs = Path(subtitles_file).resolve()
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_file),
        "-i", str(audio_abs),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-vf", f"subtitles={subtitles_abs}:force_style='Fontsize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000FF,BorderStyle=3'",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=600, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg failed: {result.stderr}")
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        logger.info(f"Final video with audio/subtitles: {output_file}")
        
        # Clean up intermediate file
        Path(video_file).unlink(missing_ok=True)
        
        return str(output_file)
        
    except Exception as e:
        logger.error(f"Failed to add audio/subtitles: {e}")
        raise
