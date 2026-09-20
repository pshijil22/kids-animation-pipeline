"""
Video composition - Use FFmpeg to create final MP4 from scenes + audio + subtitles
"""
import os
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

VIDEOS_DIR = Path("/data/videos")
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# Video settings from environment
VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', 1280))
VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', 720))
VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))
VIDEO_BITRATE = os.getenv('VIDEO_BITRATE', '2500k')


async def create_video(story: dict, audio_data: dict, scene_data: dict, job_id: str) -> dict:
    """
    Compose final video: scenes + audio + subtitles using FFmpeg.
    
    Args:
        story: Story metadata
        audio_data: Audio files (narration_file, subtitles_file, total_duration)
        scene_data: Scene images (scene_images list)
        job_id: Unique job ID
    
    Returns:
        dict: Contains video_file path and metadata
    """
    
    logger.info(f"Creating video for job {job_id}")
    
    try:
        # Input files
        narration_file = audio_data['narration_file']
        subtitles_file = audio_data['subtitles_file']
        scene_images = scene_data['scene_images']
        total_duration = audio_data['total_duration']
        
        # Output file
        video_file = VIDEOS_DIR / f"{job_id}.mp4"
        
        # Create concat file for image sequence
        concat_file = VIDEOS_DIR / f"{job_id}_concat.txt"
        duration_per_scene = total_duration / len(scene_images)
        
        logger.info(f"Duration per scene: {duration_per_scene:.2f}s")
        
        with open(concat_file, 'w') as f:
            for scene in scene_images:
                f.write(f"file '{scene['path']}'\n")
                f.write(f"duration {duration_per_scene:.2f}\n")
            # Repeat last image to fill remaining time
            f.write(f"file '{scene_images[-1]['path']}'\n")
        
        logger.info(f"Concat file created: {concat_file}")
        
        # FFmpeg command: images + audio + subtitles → MP4
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),  # Image sequence
            "-i", str(narration_file),  # Audio
            "-vf", f"subtitles={subtitles_file}:force_style='Fontsize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000FF'",  # Subtitles
            "-c:v", "libx264",  # H.264 codec
            "-preset", "medium",  # Compression (fast/medium/slow)
            "-b:v", VIDEO_BITRATE,  # Video bitrate
            "-c:a", "aac",  # Audio codec
            "-b:a", "128k",  # Audio bitrate
            "-pix_fmt", "yuv420p",  # YouTube-compatible pixel format
            "-movflags", "+faststart",  # Enable streaming
            str(video_file)
        ]
        
        logger.info(f"Running FFmpeg: {' '.join(cmd[:5])}...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=600,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg failed: {result.stderr}")
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        logger.info(f"Video created successfully: {video_file}")
        
        # Get file size
        file_size = video_file.stat().st_size
        logger.info(f"Video size: {file_size / 1024 / 1024:.2f} MB")
        
        # Clean up concat file
        concat_file.unlink()
        
        return {
            'video_file': str(video_file),
            'title': story['title'],
            'description': story['description'],
            'size_bytes': file_size,
            'duration_seconds': total_duration,
            'job_id': job_id
        }
        
    except Exception as e:
        logger.error(f"Video creation failed: {e}")
        raise
