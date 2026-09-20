"""
Story generation via Ollama LLM
Handles LLM communication, retries, and JSON parsing
"""
import os
import json
import asyncio
import logging
import re
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://ollama:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')

async def wait_for_ollama(max_retries=30, delay=1):
    """
    Wait for Ollama to be ready.
    Retries every `delay` seconds up to `max_retries` times.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            if response.status_code == 200:
                logger.info(f"Ollama is ready (attempt {attempt + 1})")
                return True
        except Exception:
            pass
        
        if attempt < max_retries - 1:
            logger.warning(f"Ollama not ready, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(delay)
    
    raise Exception(f"Ollama not responding after {max_retries} attempts at {OLLAMA_URL}")

async def generate_story_with_llm(max_retries=3):
    """
    Call Ollama to generate a story.
    Retries on failure.
    
    Returns:
        str: Raw JSON text from LLM
    """
    
    # Wait for Ollama to be ready
    await wait_for_ollama()
    
    # Load the prompt
    prompt_file = Path("/app/prompts/story.txt")
    with open(prompt_file, 'r') as f:
        prompt = f.read()
    
    logger.info(f"Using model: {OLLAMA_MODEL}")
    logger.debug(f"Prompt: {prompt[:200]}...")
    
    # Try to generate, with retries
    for attempt in range(max_retries):
        try:
            logger.info(f"LLM call attempt {attempt + 1}/{max_retries}")
            
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama returned {response.status_code}: {response.text}")
            
            data = response.json()
            story_text = data.get('response', '')
            
            if not story_text:
                raise Exception("Ollama returned empty response")
            
            logger.info("LLM generation successful")
            return story_text
            
        except Exception as e:
            logger.warning(f"LLM call failed: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.info(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                raise
    
    raise Exception("All LLM retries exhausted")

def validate_story_json(raw_text):
    """
    Extract and validate JSON from LLM output.
    The LLM might include explanation text before/after JSON.
    
    Returns:
        dict: Validated story structure
    
    Raises:
        ValueError: If JSON is invalid or incomplete
    """
    
    logger.info("Parsing JSON from LLM output")
    
    # Try direct parse first
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass
    
    # Extract JSON block from text (LLM may include explanation)
    # Look for { ... }
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if json_match:
        json_text = json_match.group(0)
        try:
            story = json.loads(json_text)
            logger.info("Successfully extracted JSON from text")
            return story
        except json.JSONDecodeError as e:
            logger.warning(f"Extracted JSON is invalid: {e}")
    
    raise ValueError(
        "Could not parse valid JSON from LLM output. "
        "The model may need fine-tuning or a different prompt."
    )

def repair_story_json(story_dict):
    """
    Basic repair of missing/invalid story fields.
    Ensures minimum required fields exist.
    """
    
    # Set defaults
    if 'title' not in story_dict or not story_dict['title']:
        story_dict['title'] = "Untitled Story"
    
    if 'description' not in story_dict or not story_dict['description']:
        story_dict['description'] = "A story for children"
    
    if 'lesson' not in story_dict or not story_dict['lesson']:
        story_dict['lesson'] = "Life is an adventure"
    
    if 'age_range' not in story_dict:
        story_dict['age_range'] = "4-8"
    
    if 'scenes' not in story_dict or not isinstance(story_dict['scenes'], list):
        raise ValueError("Story must have 'scenes' array")
    
    if len(story_dict['scenes']) == 0:
        raise ValueError("Story must have at least one scene")
    
    # Validate each scene
    for i, scene in enumerate(story_dict['scenes']):
        if 'number' not in scene:
            scene['number'] = i + 1
        if 'narration' not in scene or not scene['narration']:
            scene['narration'] = "..."
        if 'visual_description' not in scene or not scene['visual_description']:
            scene['visual_description'] = "A scene in the story"
        if 'duration_seconds' not in scene:
            scene['duration_seconds'] = 10
    
    logger.info(f"Repaired story: {len(story_dict['scenes'])} scenes")
    return story_dict
