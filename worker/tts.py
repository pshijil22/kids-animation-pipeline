"""
Text-to-Speech Generation using eSpeak-ng
Converts story narration to audio WAV files
"""
import os
import subprocess
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

AUDIO_DIR = Path("./data/audio")

async def generate_narration_from_story(story: dict, job_id: str) -> dict:
    """
    Generate narration audio from story scenes.
    
    Args:
        story: Story dict with scenes containing 'narration' field
        job_id: Unique job ID for file naming
    
    Returns:
        dict: Contains:
            - narration_file: Path to combined narration WAV
            - scene_narrations: List of (scene_num, audio_path, duration)
            - subtitles_file: Path to SRT file
            - total_duration: Total video duration in seconds
    """
    
    # Create audio directory on first use
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating narration for job {job_id}")
    
    scene_files = []
    total_duration = 0
    subtitle_entries = []
    current_time = 0
    
    # Generate audio for each scene
    for i, scene in enumerate(story.get('scenes', []), 1):
        narration_text = scene.get('narration', '')
        scene_duration = scene.get('duration_seconds', 10)
        
        if not narration_text:
            logger.warning(f"Scene {i} has no narration text, skipping")
            continue
        
        logger.info(f"Generating audio for scene {i}: {narration_text[:50]}...")
        
        # Generate WAV file for this scene
        scene_audio_file = AUDIO_DIR / f"{job_id}_scene_{i:02d}.wav"
        
        try:
            # Use espeak-ng to generate audio
            result = subprocess.run(
                [
                    "espeak-ng",
                    "-w", str(scene_audio_file),  # Output file
                    "-s", "150",                   # Speed (words per minute)
                    "-p", "50",                    # Pitch
                    "--", narration_text           # Text to speak (-- separates options from text)
                ],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"eSpeak-ng failed for scene {i}: {result.stderr}")
                raise Exception(f"TTS failed: {result.stderr}")
            
            # Get actual audio duration
            audio_duration = get_audio_duration(str(scene_audio_file))
            logger.info(f"Scene {i} audio generated: {audio_duration:.2f}s")
            
            # Record for combining later
            scene_files.append({
                'path': str(scene_audio_file),
                'duration': audio_duration,
                'scene_num': i,
                'text': narration_text
            })
            
            # Add subtitle entry
            start_time = format_srt_time(current_time)
            end_time = format_srt_time(current_time + audio_duration)
            
            subtitle_entries.append({
                'index': i,
                'start': start_time,
                'end': end_time,
                'text': narration_text,
                'scene_title': scene.get('title', f'Scene {i}')
            })
            
            current_time += audio_duration
            total_duration += audio_duration
            
        except Exception as e:
            logger.error(f"Failed to generate audio for scene {i}: {str(e)}")
            raise
    
    # Combine all scene audio files into single narration file
    narration_file = AUDIO_DIR / f"{job_id}_narration.wav"
    combine_audio_files(scene_files, str(narration_file))
    logger.info(f"Combined narration saved: {narration_file}")
    
    # Generate SRT subtitles file
    subtitles_file = generate_subtitles(job_id, subtitle_entries)
    logger.info(f"Subtitles generated: {subtitles_file}")
    
    return {
        'narration_file': str(narration_file),
        'scene_narrations': scene_files,
        'subtitles_file': str(subtitles_file),
        'total_duration': total_duration
    }


def get_audio_duration(audio_file: str) -> float:
    """
    Get duration of audio file in seconds using ffprobe.
    
    Args:
        audio_file: Path to audio file
    
    Returns:
        float: Duration in seconds
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1:noprint_wrappers=1",
                audio_file
            ],
            capture_output=True,
            timeout=10,
            text=True
        )
        
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return duration
        else:
            logger.warning(f"Could not get duration of {audio_file}, using default")
            return 10.0
    except Exception as e:
        logger.error(f"Error getting audio duration: {e}")
        return 10.0


def combine_audio_files(scene_files: list, output_file: str) -> None:
    """
    Combine multiple WAV files into a single file using ffmpeg.
    
    Args:
        scene_files: List of dicts with 'path' and 'duration' keys
        output_file: Path to output combined WAV
    """
    if not scene_files:
        logger.warning("No scene files to combine")
        return
    
    # Create concat demuxer file for ffmpeg
    concat_file = Path(output_file).parent / f"{Path(output_file).stem}_concat.txt"
    
    with open(concat_file, 'w') as f:
        for scene in scene_files:
            # Escape file path for concat demuxer
            file_path = scene['path'].replace("'", "'\\''")
            f.write(f"file '{file_path}'\n")
    
    try:
        # Use ffmpeg concat demuxer to combine files
        subprocess.run(
            [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                output_file
            ],
            capture_output=True,
            timeout=60,
            check=True
        )
        
        logger.info(f"Audio files combined: {output_file}")
        
        # Clean up concat file
        concat_file.unlink()
        
    except Exception as e:
        logger.error(f"Failed to combine audio files: {e}")
        raise


def generate_subtitles(job_id: str, subtitle_entries: list) -> str:
    """
    Generate SRT subtitle file from narration timing.
    
    Args:
        job_id: Job ID for file naming
        subtitle_entries: List of dicts with 'start', 'end', 'text', 'scene_title'
    
    Returns:
        str: Path to generated SRT file
    """
    srt_file = AUDIO_DIR / f"{job_id}_subtitles.srt"
    
    with open(srt_file, 'w', encoding='utf-8') as f:
        for entry in subtitle_entries:
            # SRT format:
            # index
            # start --> end
            # text
            # (blank line)
            f.write(f"{entry['index']}\n")
            f.write(f"{entry['start']} --> {entry['end']}\n")
            f.write(f"{entry['scene_title']}\n")
            f.write(f"{entry['text']}\n")
            f.write("\n")
    
    logger.info(f"Subtitles saved: {srt_file}")
    return str(srt_file)


def format_srt_time(seconds: float) -> str:
    """
    Format seconds as SRT time format: HH:MM:SS,mmm
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        str: Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
