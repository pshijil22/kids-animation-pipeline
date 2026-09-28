"""
Video composition - Create final MP4 from scenes + audio + subtitles
Production-ready with comprehensive error handling
"""
import os
import logging
import subprocess
from pathlib import Path
import time

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
VIDEOS_DIR = DATA_DIR / 'videos'

VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', 1280))
VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', 720))
VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))


async def create_animated_video(story: dict, audio_data: dict, scene_data: dict, job_id: str) -> dict:
    """
    Create final video with comprehensive error handling.
    """
    
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Creating video for job {job_id}")
    
    try:
        narration_file = Path(audio_data['narration_file'])
        subtitles_file = Path(audio_data['subtitles_file'])
        scene_images = scene_data['scene_images']
        total_duration = audio_data['total_duration']
        
        # Verify input files exist
        if not narration_file.exists():
            raise FileNotFoundError(f"Narration file missing: {narration_file}")
        if not subtitles_file.exists():
            raise FileNotFoundError(f"Subtitles file missing: {subtitles_file}")
        
        for scene in scene_images:
            scene_path = Path(scene['path'])
            if not scene_path.exists():
                raise FileNotFoundError(f"Scene image missing: {scene_path}")
        
        output_file = VIDEOS_DIR / f"{job_id}.mp4"
        intermediate_file = VIDEOS_DIR / f"{job_id}_temp.mp4"
        
        duration_per_scene = total_duration / len(scene_images)
        
        logger.info(f"Pass 1: Concatenating {len(scene_images)} scenes")
        
        # PASS 1: Create video with audio (no subtitles - simpler, more reliable)
        cmd1 = ["ffmpeg", "-y", "-loglevel", "warning"]
        
        # Add images
        for scene in scene_images:
            cmd1.extend([
                "-loop", "1",
                "-t", str(duration_per_scene),
                "-i", str(scene['path'])
            ])
        
        # Add audio
        cmd1.extend(["-i", str(narration_file)])
        
        # Build concat filter
        n_scenes = len(scene_images)
        concat_filter = "".join([f"[{i}:v]" for i in range(n_scenes)]) + f"concat=n={n_scenes}:v=1:a=0[v]"
        
        # Scale to target resolution
        full_filter = concat_filter + f",scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2[vout]"
        
        cmd1.extend([
            "-filter_complex", full_filter,
            "-map", "[vout]",
            "-map", str(n_scenes) + ":a:0?",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            str(intermediate_file)
        ])
        
        logger.info("Running FFmpeg pass 1...")
        result1 = subprocess.run(cmd1, capture_output=True, timeout=600, text=True)
        
        if result1.returncode != 0:
            logger.error(f"Pass 1 stderr: {result1.stderr}")
            # If first pass fails, try with default audio mapping
            logger.info("Retrying pass 1 with simpler audio mapping...")
            cmd1_retry = cmd1[:-2] + ["-shortest", str(intermediate_file)]
            result1 = subprocess.run(cmd1_retry, capture_output=True, timeout=600, text=True)
            if result1.returncode != 0:
                raise Exception(f"Pass 1 failed even after retry")
        
        if not intermediate_file.exists():
            raise Exception("Pass 1 created no output file")
        
        logger.info(f"Pass 1 complete")
        
        # PASS 2: Add subtitles
        logger.info("Pass 2: Adding subtitles...")
        
        cmd2 = [
            "ffmpeg", "-y", "-loglevel", "warning",
            "-i", str(intermediate_file),
            "-vf", f"subtitles={subtitles_file}:force_style='Fontsize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000FF,BorderStyle=3'",
            "-c:a", "aac",
            "-b:a", "128k",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_file)
        ]
        
        result2 = subprocess.run(cmd2, capture_output=True, timeout=600, text=True)
        
        if result2.returncode != 0:
            logger.warning(f"Pass 2 (subtitles) failed, creating video without subtitles")
            # Fallback: copy intermediate without subtitles
            import shutil
            shutil.copy(intermediate_file, output_file)
            logger.info("Video created without subtitles (fallback)")
        else:
            logger.info("Pass 2 complete with subtitles")
        
        # Verify output
        if not output_file.exists():
            raise Exception("No output video created")
        
        file_size = output_file.stat().st_size
        if file_size < 100000:  # Less than 100KB = likely corrupted
            raise Exception(f"Output video suspiciously small: {file_size} bytes")
        
        logger.info(f"Video created: {output_file} ({file_size / 1024 / 1024:.2f} MB)")
        
        # Clean up
        intermediate_file.unlink(missing_ok=True)
        
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
        logger.error(f"Video creation failed: {e}", exc_info=True)
        raise
