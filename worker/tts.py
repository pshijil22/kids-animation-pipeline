"""
Text-to-Speech Generation using eSpeak-ng
Production-ready with error handling and fallbacks
"""
import os
import subprocess
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
AUDIO_DIR = DATA_DIR / 'audio'

AUDIO_DIR.mkdir(parents=True, exist_ok=True)


async def generate_narration_from_story(story: dict, job_id: str) -> dict:
    """
    Generate narration audio from story scenes with comprehensive error handling.
    """
    
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
        
        if not narration_text or not narration_text.strip():
            logger.warning(f"Scene {i} has no narration, using placeholder")
            narration_text = "..."
        
        logger.info(f"Scene {i}: {narration_text[:50]}...")
        
        scene_audio_file = AUDIO_DIR / f"{job_id}_scene_{i:02d}.wav"
        
        try:
            # Use espeak-ng with safe defaults
            result = subprocess.run(
                [
                    "espeak-ng",
                    "-w", str(scene_audio_file),
                    "-s", "150",
                    "-p", "50",
                    "--",
                    narration_text[:500]  # Limit text length
                ],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"eSpeak failed for scene {i}: {result.stderr}")
                # Create silent audio fallback
                _create_silent_audio(str(scene_audio_file), scene_duration)
            
            # Get audio duration
            audio_duration = _get_audio_duration(str(scene_audio_file))
            if audio_duration <= 0:
                audio_duration = scene_duration
            
            logger.info(f"Scene {i}: {audio_duration:.2f}s")
            
            scene_files.append({
                'path': str(scene_audio_file),
                'duration': audio_duration,
                'scene_num': i,
                'text': narration_text
            })
            
            # Subtitle entry
            start_time = _format_srt_time(current_time)
            end_time = _format_srt_time(current_time + audio_duration)
            
            subtitle_entries.append({
                'index': i,
                'start': start_time,
                'end': end_time,
                'text': narration_text[:200],
                'scene_title': scene.get('title', f'Scene {i}')
            })
            
            current_time += audio_duration
            total_duration += audio_duration
            
        except Exception as e:
            logger.error(f"Scene {i} failed: {e}")
            # Create minimal audio
            _create_silent_audio(str(scene_audio_file), scene_duration)
            scene_files.append({
                'path': str(scene_audio_file),
                'duration': scene_duration,
                'scene_num': i,
                'text': narration_text
            })
            total_duration += scene_duration
    
    # Combine audio files
    narration_file = AUDIO_DIR / f"{job_id}_narration.wav"
    _combine_audio_files(scene_files, str(narration_file))
    
    # Generate subtitles
    subtitles_file = _generate_subtitles(job_id, subtitle_entries)
    
    logger.info(f"Narration complete: {total_duration:.2f}s")
    
    return {
        'narration_file': str(narration_file),
        'scene_narrations': scene_files,
        'subtitles_file': str(subtitles_file),
        'total_duration': total_duration
    }


def _create_silent_audio(output_file: str, duration: float) -> None:
    """Create silent audio file as fallback."""
    import struct
    sample_rate = 22050
    num_samples = int(sample_rate * duration)
    
    try:
        with open(output_file, 'wb') as f:
            # WAV header
            f.write(b'RIFF')
            f.write(struct.pack('<I', 36 + num_samples * 2))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write(struct.pack('<I', 16))
            f.write(struct.pack('<HHIIHH', 1, 1, sample_rate, sample_rate * 2, 2, 16))
            f.write(b'data')
            f.write(struct.pack('<I', num_samples * 2))
            # Silent audio (zeros)
            f.write(b'\x00' * (num_samples * 2))
        logger.info(f"Created silent audio: {output_file}")
    except Exception as e:
        logger.error(f"Failed to create silent audio: {e}")


def _get_audio_duration(audio_file: str) -> float:
    """Get audio duration, with error handling."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_file
            ],
            capture_output=True,
            timeout=10,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Could not get duration: {e}")
    
    return 0.0


def _combine_audio_files(scene_files: list, output_file: str) -> None:
    """Combine audio files with error handling."""
    if not scene_files:
        logger.warning("No audio files to combine")
        return
    
    concat_file = Path(output_file).parent / f"{Path(output_file).stem}_concat.txt"
    
    try:
        with open(concat_file, 'w') as f:
            for scene in scene_files:
                abs_path = Path(scene['path']).resolve()
                f.write(f"file '{abs_path}'\n")
        
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), 
             "-c", "copy", output_file],
            capture_output=True,
            timeout=60,
            text=True
        )
        
        if result.returncode != 0:
            logger.warning(f"Audio combine failed, using first file: {result.stderr}")
            import shutil
            shutil.copy(scene_files[0]['path'], output_file)
        
        logger.info(f"Audio combined: {output_file}")
        concat_file.unlink(missing_ok=True)
        
    except Exception as e:
        logger.error(f"Audio combine error: {e}")
        import shutil
        if scene_files:
            shutil.copy(scene_files[0]['path'], output_file)


def _generate_subtitles(job_id: str, subtitle_entries: list) -> str:
    """Generate SRT subtitles."""
    srt_file = AUDIO_DIR / f"{job_id}_subtitles.srt"
    
    try:
        with open(srt_file, 'w', encoding='utf-8') as f:
            for entry in subtitle_entries:
                f.write(f"{entry['index']}\n")
                f.write(f"{entry['start']} --> {entry['end']}\n")
                f.write(f"{entry['scene_title']}\n")
                f.write(f"{entry['text']}\n\n")
        logger.info(f"Subtitles generated: {srt_file}")
    except Exception as e:
        logger.error(f"Subtitle generation failed: {e}")
    
    return str(srt_file)


def _format_srt_time(seconds: float) -> str:
    """Format time for SRT."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
