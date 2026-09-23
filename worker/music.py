"""
Background Music Integration
Adds royalty-free background music to videos
"""
import logging
import os
import subprocess
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

# Use environment variable for data directory
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
MUSIC_DIR = DATA_DIR / 'music'

# Music settings
MUSIC_SOURCE = os.getenv('MUSIC_SOURCE', 'local')  # 'local', 'youtube', or 'freesound'
MUSIC_VOLUME = float(os.getenv('MUSIC_VOLUME', '0.3'))  # Background volume
NARRATION_VOLUME = float(os.getenv('NARRATION_VOLUME', '1.0'))  # Narration volume


async def add_background_music(video_file: str, audio_file: str, total_duration: float, job_id: str, music_file: str = None) -> str:
    """
    Add background music to video.
    
    Args:
        video_file: Path to video file
        audio_file: Path to narration audio
        total_duration: Duration in seconds
        job_id: Unique job ID
        music_file: Optional custom music file path
    
    Returns:
        str: Path to final video with music
    """
    
    logger.info("Adding background music...")
    
    if not music_file:
        # Try to find or download music
        music_file = await _get_background_music(total_duration, job_id)
    
    if not music_file or not Path(music_file).exists():
        logger.warning("No background music found, skipping")
        return video_file
    
    try:
        output_file = str(Path(video_file).parent / f"{Path(video_file).stem}_with_music.mp4")
        
        # Mix audio: narration + background music
        mixed_audio = _mix_audio(audio_file, music_file, total_duration, job_id)
        
        # Add mixed audio to video
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_file),
            "-i", str(mixed_audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=600, text=True)
        if result.returncode != 0:
            logger.warning(f"Failed to add music: {result.stderr}")
            return video_file
        
        logger.info(f"Video with background music: {output_file}")
        
        # Clean up
        Path(mixed_audio).unlink(missing_ok=True)
        Path(video_file).unlink(missing_ok=True)
        
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to add background music: {e}")
        return video_file


async def _get_background_music(duration: float, job_id: str) -> str:
    """
    Get background music for the video.
    Returns path to music file if available.
    """
    
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    
    # Free music sources (Creative Commons)
    music_sources = [
        'https://www.bensound.com/download/ukulele',  # Bensound
        'https://www.incompetech.com/music/',  # Incompetech
    ]
    
    logger.info("Background music support available but requires manual setup")
    logger.info("Suggested: Place .mp3 or .wav files in credentials/music/ directory")
    logger.info("Or set MUSIC_FILE env var to absolute path")
    
    # Check for user-provided music
    user_music = Path(os.getenv('MUSIC_FILE', ''))
    if user_music.exists():
        logger.info(f"Using provided music: {user_music}")
        return str(user_music)
    
    return None


def _mix_audio(narration_file: str, music_file: str, total_duration: float, job_id: str) -> str:
    """
    Mix narration and background music using FFmpeg.
    Narration: full volume, Music: background volume with fade in/out.
    """
    import subprocess
    
    output_file = Path(narration_file).parent / f"{Path(narration_file).stem}_mixed_{job_id}.wav"
    
    # Build audio filter: narration at full volume, music at background volume with fadeout
    audio_filter = f"[1:a]volume={MUSIC_VOLUME},afade=t=out:st={max(total_duration-2, 0)}:d=2[music];[0:a]volume={NARRATION_VOLUME}[narration];[narration][music]amix=inputs=2:duration=first"
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(narration_file),
        "-i", str(music_file),
        "-filter_complex", audio_filter,
        "-c:a", "pcm_s16le",
        "-ar", "48000",
        str(output_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300, text=True)
        if result.returncode != 0:
            logger.warning(f"Audio mixing failed: {result.stderr}")
            return narration_file  # Return original if mixing fails
        
        logger.info(f"Audio mixed: {output_file}")
        return str(output_file)
        
    except Exception as e:
        logger.error(f"Failed to mix audio: {e}")
        return narration_file
