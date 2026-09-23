"""
Professional Text-to-Speech using Google Cloud
Generates high-quality narration with multiple voice options
"""
import logging
import os
from pathlib import Path
from typing import Dict
import asyncio

logger = logging.getLogger(__name__)

try:
    from google.cloud import texttospeech
    GCP_TTS_AVAILABLE = True
except ImportError:
    GCP_TTS_AVAILABLE = False
    logger.warning("Google Cloud TTS not available")

# Use environment variable for data directory
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
AUDIO_DIR = DATA_DIR / 'audio'

# Google Cloud TTS settings
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', '')
GCP_CREDENTIALS = os.getenv('GCP_CREDENTIALS', '')

# Voice settings
VOICE_NAME = os.getenv('GCP_VOICE_NAME', 'en-US-Neural2-C')  # Professional female voice
SPEAKING_RATE = float(os.getenv('GCP_SPEAKING_RATE', '1.0'))
PITCH = float(os.getenv('GCP_PITCH', '0.0'))


async def generate_professional_narration(story: dict, job_id: str) -> dict:
    """
    Generate professional narration using Google Cloud Text-to-Speech.
    
    Args:
        story: Story dict with scenes containing 'narration' field
        job_id: Unique job ID for file naming
    
    Returns:
        dict: Contains narration_file, scene_narrations, subtitles_file, total_duration
    """
    
    # Create audio directory on first use
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    if not GCP_TTS_AVAILABLE or not GCP_PROJECT_ID:
        logger.warning("Google Cloud TTS not configured, using eSpeak fallback")
        from tts import generate_narration_from_story
        return await generate_narration_from_story(story, job_id)
    
    logger.info(f"Generating professional narration for job {job_id}")
    logger.info(f"Using voice: {VOICE_NAME}")
    
    try:
        # Initialize TTS client
        client = texttospeech.TextToSpeechClient()
        
        scene_files = []
        total_duration = 0
        subtitle_entries = []
        current_time = 0
        
        # Generate audio for each scene
        for i, scene in enumerate(story.get('scenes', []), 1):
            narration_text = scene.get('narration', '')
            scene_duration = scene.get('duration_seconds', 10)
            
            if not narration_text:
                logger.warning(f"Scene {i} has no narration text")
                continue
            
            logger.info(f"Generating audio for scene {i}...")
            
            try:
                # Create TTS request
                synthesis_input = texttospeech.SynthesisInput(text=narration_text)
                
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    name=VOICE_NAME
                )
                
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                    speaking_rate=SPEAKING_RATE,
                    pitch=PITCH
                )
                
                # Generate speech
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                
                # Save audio file
                scene_audio_file = AUDIO_DIR / f"{job_id}_scene_{i:02d}.wav"
                with open(scene_audio_file, 'wb') as out:
                    out.write(response.audio_content)
                
                logger.info(f"Scene {i} audio generated: {scene_audio_file}")
                
                # Get audio duration (estimate from text length)
                # Rough estimate: ~3 characters per word, ~150 words per minute
                word_count = len(narration_text.split())
                audio_duration = max(word_count / 2.5, 3.0)  # At least 3 seconds
                
                scene_files.append({
                    'path': str(scene_audio_file),
                    'duration': audio_duration,
                    'scene_num': i,
                    'text': narration_text
                })
                
                # Add subtitle entry
                start_time = _format_srt_time(current_time)
                end_time = _format_srt_time(current_time + audio_duration)
                
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
                logger.error(f"Failed to generate audio for scene {i}: {e}")
                raise
        
        # Combine audio files
        narration_file = AUDIO_DIR / f"{job_id}_narration.wav"
        _combine_audio_files(scene_files, str(narration_file))
        logger.info(f"Combined narration saved: {narration_file}")
        
        # Generate subtitles
        subtitles_file = _generate_subtitles(job_id, subtitle_entries)
        logger.info(f"Subtitles generated: {subtitles_file}")
        
        return {
            'narration_file': str(narration_file),
            'scene_narrations': scene_files,
            'subtitles_file': str(subtitles_file),
            'total_duration': total_duration
        }
        
    except Exception as e:
        logger.error(f"Professional narration generation failed: {e}")
        raise


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT time: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _combine_audio_files(scene_files: list, output_file: str) -> None:
    """Combine multiple WAV files into single file."""
    import subprocess
    from pathlib import Path
    
    if not scene_files:
        logger.warning("No audio files to combine")
        return
    
    concat_file = Path(output_file).parent / f"{Path(output_file).stem}_concat.txt"
    
    with open(concat_file, 'w') as f:
        for scene in scene_files:
            abs_path = Path(scene['path']).resolve()
            f.write(f"file '{abs_path}'\n")
    
    try:
        result = subprocess.run(
            ["ffmpeg", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", output_file],
            capture_output=True,
            timeout=60,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")
        
        logger.info(f"Audio files combined: {output_file}")
        concat_file.unlink()
        
    except Exception as e:
        logger.error(f"Failed to combine audio files: {e}")
        raise


def _generate_subtitles(job_id: str, subtitle_entries: list) -> str:
    """Generate SRT subtitle file."""
    srt_file = AUDIO_DIR / f"{job_id}_subtitles.srt"
    
    with open(srt_file, 'w', encoding='utf-8') as f:
        for entry in subtitle_entries:
            f.write(f"{entry['index']}\n")
            f.write(f"{entry['start']} --> {entry['end']}\n")
            f.write(f"{entry['scene_title']}\n")
            f.write(f"{entry['text']}\n\n")
    
    return str(srt_file)
