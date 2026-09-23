"""
Video composition - Create final MP4 from scenes + audio + subtitles
Uses FFmpeg with simple, reliable slideshow approach
"""
import os
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Use environment variable for data directory
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
VIDEOS_DIR = DATA_DIR / 'videos'

# Video settings from environment
VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', 1280))
VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', 720))
VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))
VIDEO_BITRATE = os.getenv('VIDEO_BITRATE', '2500k')


async def create_animated_video(story: dict, audio_data: dict, scene_data: dict, job_id: str) -> dict:
    """
    Create final video: scenes + audio + subtitles using FFmpeg.
    Uses simple, reliable slideshow approach.
    
    Args:
        story: Story metadata
        audio_data: Audio files (narration_file, subtitles_file, total_duration)
        scene_data: Scene images (scene_images list)
        job_id: Unique job ID
    
    Returns:
        dict: Contains video_file path and metadata
    """
    
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Creating video for job {job_id}")
    logger.info(f"Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} @ {VIDEO_FPS} FPS")
    
    try:
        narration_file = audio_data['narration_file']
        subtitles_file = audio_data['subtitles_file']
        scene_images = scene_data['scene_images']
        total_duration = audio_data['total_duration']
        
        output_file = VIDEOS_DIR / f"{job_id}.mp4"
        
        # Create simple slideshow: each scene lasts duration_per_scene seconds
        duration_per_scene = total_duration / len(scene_images)
        
        logger.info(f"Creating slideshow: {len(scene_images)} scenes @ {duration_per_scene:.2f}s each")
        
        # Build FFmpeg command with image inputs
        cmd = ["ffmpeg", "-y"]
        
        # Add each image with duration
        for scene in scene_images:
            cmd.extend([
                "-loop", "1",
                "-t", str(duration_per_scene),
                "-i", scene['path']
            ])
        
        # Concat filter: concatenate all video inputs
        n_scenes = len(scene_images)
        concat_filter = "".join([f"[{i}:v]" for i in range(n_scenes)]) + f"concat=n={n_scenes}:v=1:a=0[v]"
        
        # Add audio input
        cmd.extend(["-i", str(narration_file)])
        
        # Build final command
        cmd.extend([
            "-filter_complex", concat_filter,
            "-map", "[v]",
            "-map", str(n_scenes) + ":a:0",
            "-vf", f"subtitles={subtitles_file}:force_style='Fontsize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000FF'",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_file)
        ])
        
        logger.info("Running FFmpeg to create video...")
        
        result = subprocess.run(cmd, capture_output=True, timeout=600, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg stderr: {result.stderr[-500:]}")  # Last 500 chars
            raise Exception(f"FFmpeg failed")
        
        logger.info(f"Video created: {output_file}")
        
        # Get file size
        file_size = output_file.stat().st_size
        logger.info(f"Video size: {file_size / 1024 / 1024:.2f} MB")
        
        return {
            'video_file': str(output_file),
            'title': story['title'],
            'description': story['description'],
            'size_bytes': file_size,
            'duration_seconds': total_duration,
            'job_id': job_id,
            'resolution': f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
            'fps': VIDEO_FPS
        }
        
    except Exception as e:
        logger.error(f"Video creation failed: {e}")
        raise
